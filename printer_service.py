import socket
from click.core import F
from escpos.printer import Network
from escpos.exceptions import Error as EscposError
from models import PrintStationGroup, InvoiceRequest
from datetime import datetime

class PrinterService:
    def __init__(self):
        self.encoding = "cp858"  # Codificación que soporta caracteres especiales

    def test_printer_connection(self, printer_ip: str) -> bool:
        """Prueba la conectividad con una impresora"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            result = sock.connect_ex((printer_ip, 9100))
            sock.close()
            return result == 0
        except Exception:
            return False

    def format_currency(self, amount: float) -> str:
        """Formatea moneda en pesos colombianos"""
        return f"${amount:,.0f}"

    def print_order_to_station(
        self, station_group: PrintStationGroup, order_data: dict
    ) -> bool:
        """Imprime una comanda en una estación específica"""
        try:
            printer = Network(station_group.print_station.printer_ip)

            # Configurar codificación para caracteres especiales
            printer.charcode("CP858")

            # Encabezado con el nombre de la estación
            printer.set(align="center", bold=True, double_width=True, double_height=True)
            printer.text(f"{station_group.print_station.name}\n")
            printer.text("=" * 24 + "\n")

            # Información de la orden (fuente pequeña)
            printer.set(align="left", bold=False, double_width=False, double_height=False, font='b')
            printer.text(f"Orden: #{order_data['order_id']}\n")
            printer.text(f"Mesa: {order_data['table_number']}\n")
            printer.text(f"Numero de personas: {order_data['diners_count']}\n")
            printer.text(f"Mesero: {order_data['waiter_name']}\n")
            printer.text(f"{datetime.now().strftime('%d/%m/%Y %H:%M')}\n")

            if order_data.get("order_notes"):
                printer.text(f"Notas: {order_data['order_notes']}\n")

            # Resetear fuente a normal
            printer.set(font='a')
            printer.text("-" * 24 + "\n")

            # Agrupar items por nombre para consolidar cantidades
            items_consolidated = {}
            for item in station_group.items:
                # Crear clave única basada en el item y sus características
                item_key = f"{item.menu_item_name}"
                if item.cooking_point:
                    item_key += f"__{item.cooking_point.name}"
                if item.sides:
                    sides_key = "_".join(sorted([side.name for side in item.sides]))
                    item_key += f"__{sides_key}"
                if item.notes:
                    item_key += f"__{item.notes}"

                if item_key not in items_consolidated:
                    items_consolidated[item_key] = {
                        "menu_item_name": item.menu_item_name,
                        "quantity": 0,
                        "cooking_point": item.cooking_point,
                        "sides": item.sides,
                        "notes": item.notes
                    }
                
                items_consolidated[item_key]["quantity"] += item.quantity

            # Items de la comanda consolidados
            printer.set(align="left", bold=False, double_width=False, double_height=False)
            for item_data in items_consolidated.values():
                # Nombre del item y cantidad
                printer.set(bold=True, double_height=True)
                printer.text(f"{item_data['quantity']}x {item_data['menu_item_name']}\n")

                # Punto de cocción si existe
                if item_data['cooking_point']:
                    printer.set(bold=False, double_height=False)
                    printer.text(f"   Cocción: {item_data['cooking_point'].name}\n")

                # Acompañamientos
                if item_data['sides']:
                    sides_text = ", ".join([side.name for side in item_data['sides']])
                    printer.text(f"   Con: {sides_text}\n")

                # Notas del item
                if item_data['notes']:
                    printer.text(f"   Nota: {item_data['notes']}\n")

                printer.text("\n")

            printer.text("-" * 40 + "\n")

            # Cortar papel
            printer.cut()
            printer.close()

            return True

        except EscposError as e:
            print(f"Error de impresora ESC/POS: {e}")
            return False
        except Exception as e:
            print(f"Error general al imprimir: {e}")
            return False

    def print_invoice(self, invoice_data: InvoiceRequest) -> tuple[bool, str]:
        """Imprime una factura"""
        try:
            # Para la factura, usaremos la primera impresora disponible
            # En un entorno real, esto debería ser configurable
            printer_ip = "192.168.1.79"  # IP por defecto

            if not self.test_printer_connection(printer_ip):
                return False, "No se pudo conectar con la impresora de facturación"

            printer = Network(printer_ip)
            printer.charcode("CP858")

            # Encabezado de factura
            printer.set(align="center", bold=True, double_width=True, double_height=True)
            printer.text(f"{invoice_data.restaurant_info.name}\n")
            printer.text("=" * 24 + "\n")

            # Información del restaurante
            if invoice_data.restaurant_info:
                printer.set(align="center", bold=False, double_width=False, double_height=False, font='b')
                printer.text(f"{invoice_data.restaurant_info.address}\n")
                printer.text(f"Tel: {invoice_data.restaurant_info.phone}\n")
                printer.text(f"NIT: {invoice_data.restaurant_info.tax_id}\n")
                printer.text("-" * 24 + "\n")


            # Información de la orden
            printer.set(align="left", bold=False, double_width=False, double_height=False,font='b')
            invoice_number = (
                f"FAC-{invoice_data.order_id}-{datetime.now().strftime('%Y%m%d%H%M')}"
            )
            printer.text(f"Factura: {invoice_number}\n")
            printer.text(f"Orden: #{invoice_data.order_id}\n")
            printer.text(f"Mesa: {invoice_data.table_number}\n")
            printer.text(f"Comensales: {invoice_data.diners_count}\n")
            printer.text(f"Mesero: {invoice_data.waiter_name}\n")
            printer.text(f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
            printer.text("-" * 24 + "\n")

            # Items facturados
            printer.set(align="left", bold=False, double_width=False, double_height=False, font='b')
            for item in invoice_data.items:
                printer.text(f"{item.quantity}x {item.menu_item_name}\n")
                printer.text(f"   ${item.unit_price:,.0f} c/u\n")

                printer.set(align="right")
                printer.text(f"${item.subtotal:,.0f}\n")
                printer.set(align="left")
                printer.text("\n")

            printer.text("-" * 32 + "\n")

            # Totales
            printer.set(align="right", bold=False, double_width=False, double_height=False,font='b')
            printer.text(f"Subtotal: {self.format_currency(invoice_data.subtotal)}\n")
            printer.text(
                f"INC: {self.format_currency(invoice_data.tax_amount)}\n"
            )
            printer.text(f"Propina: {self.format_currency(invoice_data.tip_amount)}\n")
            printer.text(f"Total a pagar: {self.format_currency(invoice_data.grand_total)}\n")

            # # Información de pago
            # printer.text("-" * 32 + "\n")
            # printer.set(align="left", bold=True, double_width=False, double_height=False)
            # printer.text("PAGO\n")
            # printer.set(bold=False)

            # # Usar el nombre del método enviado desde el frontend o el método como fallback
            # payment_method_display = (
            #     invoice_data.payment.payment_method_name or invoice_data.payment.method
            # )
            # printer.text(f"Método: {payment_method_display}\n")

            # if invoice_data.payment.cash_amount:
            #     printer.text(
            #         f"Efectivo: {self.format_currency(invoice_data.payment.cash_amount)}\n"
            #     )
            # if invoice_data.payment.card_amount:
            #     printer.text(
            #         f"Tarjeta: {self.format_currency(invoice_data.payment.card_amount)}\n"
            #     )
            # if invoice_data.payment.transfer_amount:
            #     printer.text(
            #         f"Transferencia: {self.format_currency(invoice_data.payment.transfer_amount)}\n"
            #     )
            # if invoice_data.payment.change_amount > 0:
            #     printer.text(
            #         f"Cambio: {self.format_currency(invoice_data.payment.change_amount)}\n"
            #     )

            # Pie de página
            printer.text("\n")
            printer.set(align="center", bold=False, double_width=False, double_height=False)
            printer.text("¡Gracias por su visita!\n")
            printer.text("Vuelva pronto\n")
            printer.text("=" * 32 + "\n")

            # Cortar papel
            printer.cut()
            printer.close()

            return True, invoice_number

        except EscposError as e:
            return False, f"Error de impresora ESC/POS: {e}"
        except Exception as e:
            return False, f"Error general al imprimir factura: {e}"
