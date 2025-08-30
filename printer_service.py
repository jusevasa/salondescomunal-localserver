import socket
from click.core import F
from escpos.printer import Network
from escpos.exceptions import Error as EscposError
from models import PrintStationGroup, InvoiceRequest
from datetime import datetime
from zoneinfo import ZoneInfo


class PrinterService:
    def __init__(self):
        self.encoding = "cp858"  # Codificación que soporta caracteres especiales

    def test_printer_connection(self, printer_ip: str) -> bool:
        """Prueba la conectividad con una impresora de forma robusta"""
        try:
            # Primero verificar conectividad básica de red
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)  # Aumentar timeout
            result = sock.connect_ex((printer_ip, 9100))
            sock.close()

            if result != 0:
                return False

            # Intentar crear una conexión real con la impresora
            printer = Network(printer_ip)

            # Enviar comando de estado para verificar que la impresora responde
            printer._raw(b"\x10\x04\x01")  # Comando DLE EOT para obtener estado

            # Si llegamos aquí, la impresora está realmente conectada
            printer.close()
            return True

        except (
            EscposError,
            socket.error,
            socket.timeout,
            ConnectionRefusedError,
            OSError,
        ) as e:
            return False
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
            printer.set(
                align="center", bold=True, double_width=True, double_height=True
            )
            printer.text(f"{station_group.print_station.name}\n")
            printer.text("=" * 24 + "\n")

            # Información de la orden (fuente pequeña)
            printer.set(
                align="left",
                bold=False,
                double_width=False,
                double_height=False,
                font="b",
            )
            printer.text(f"Orden: #{order_data['order_id']}\n")
            printer.text(f"Mesa: {order_data['table_number']}\n")
            printer.text(f"Numero de personas: {order_data['diners_count']}\n")
            printer.text(f"Mesero: {order_data['waiter_name']}\n")
            printer.text(
                f"{datetime.now(ZoneInfo('America/Bogota')).strftime('%d/%m/%Y %I:%M %p').lower()}\n"
            )

            if order_data.get("order_notes"):
                printer.text(f"Notas: {order_data['order_notes']}\n")

            # Resetear fuente a normal
            printer.set(font="a")
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
                        "notes": item.notes,
                    }

                items_consolidated[item_key]["quantity"] += item.quantity

            # Items de la comanda consolidados
            printer.set(
                align="left", bold=False, double_width=False, double_height=False
            )
            for item_data in items_consolidated.values():
                # Nombre del item y cantidad
                printer.set(bold=True, double_height=True)
                printer.text(
                    f"{item_data['quantity']}x {item_data['menu_item_name']}\n"
                )

                # Punto de cocción si existe
                if item_data["cooking_point"]:
                    printer.set(bold=False, double_height=False)
                    printer.text(f"   Cocción: {item_data['cooking_point'].name}\n")

                # Acompañamientos
                if item_data["sides"]:
                    sides_text = ", ".join([side.name for side in item_data["sides"]])
                    printer.text(f"   Con: {sides_text}\n")

                # Notas del item
                if item_data["notes"]:
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
            printer_ip = "192.168.80.65"  # IP por defecto

            if not self.test_printer_connection(printer_ip):
                return False, "No se pudo conectar con la impresora de facturación"

            printer = Network(printer_ip)
            printer.charcode("CP858")

            # Configurar fuente pequeña y compacta
            printer._raw(b"\x1b\x21\x00")  # Reset font settings

            # Encabezado de factura - compacto
            printer.set(
                align="center",
                bold=True,
                double_width=False,
                double_height=False,
                font="a",
            )
            printer.text(f"{invoice_data.restaurant_info.name}\n")
            printer.text("=" * 42 + "\n")

            # Información del restaurante - fuente pequeña
            if invoice_data.restaurant_info:
                printer.set(
                    align="center",
                    bold=False,
                    double_width=False,
                    double_height=False,
                    font="a",
                )
                printer.text(f"{invoice_data.restaurant_info.address}\n")
                printer.text(f"Tel: {invoice_data.restaurant_info.phone}\n")
                printer.text(f"{invoice_data.restaurant_info.tax_id}\n")
                printer.text("-" * 42 + "\n")

            # Información de la orden - fuente pequeña
            printer.set(
                align="left",
                bold=False,
                double_width=False,
                double_height=False,
                font="a",
            )
            invoice_number = f"FAC-{invoice_data.order_id}-{datetime.now(ZoneInfo('America/Bogota')).strftime('%Y%m%d%H%M')}"
            printer.text(f"Factura: {invoice_number}\n")
            printer.text(f"Orden: #{invoice_data.order_id}\n")
            printer.text(f"Mesa: {invoice_data.table_number}\n")
            printer.text(f"Comensales: {invoice_data.diners_count}\n")
            printer.text(f"Mesero: {invoice_data.waiter_name}\n")
            printer.text(
                f"Fecha: {datetime.now(ZoneInfo('America/Bogota')).strftime('%d/%m/%Y %I:%M %p').lower()}\n"
            )
            printer.text("-" * 42 + "\n")

            # Items facturados - formato compacto
            printer.set(
                align="left",
                bold=False,
                double_width=False,
                double_height=False,
                font="a",
            )
            for item in invoice_data.items:
                printer.text(f"{item.quantity}x {item.menu_item_name}\n")

                # Precio unitario y total en línea compacta
                price_text = f"  ${item.unit_price:,.0f} c/u"
                total_text = f"${item.subtotal:,.0f}"
                spaces_needed = 42 - len(price_text) - len(total_text)
                printer.text(
                    f"{price_text}" + " " * max(1, spaces_needed) + f"{total_text}\n"
                )

            printer.text("-" * 42 + "\n")

            # Totales - fuente pequeña
            printer.set(
                align="right",
                bold=False,
                double_width=False,
                double_height=False,
                font="a",
            )
            printer.text(f"Subtotal: {self.format_currency(invoice_data.subtotal)}\n")
            printer.text(f"INC: {self.format_currency(invoice_data.tax_amount)}\n")
            printer.text(f"Propina: {self.format_currency(invoice_data.tip_amount)}\n")

            # Total final solo en negrita
            printer.set(bold=True, font="a")
            printer.text(
                f"Total a pagar: {self.format_currency(invoice_data.grand_total)}\n"
            )

            # Pie de página - fuente pequeña
            printer.text("\n")
            printer.set(
                align="center",
                bold=False,
                double_width=False,
                double_height=False,
                font="a",
            )
            printer.text("¡Gracias por su visita!\n")
            printer.text("Vuelva pronto\n")
            printer.text("=" * 42 + "\n")

            # Cortar papel
            printer.cut()
            printer.close()

            return True, invoice_number

        except EscposError as e:
            return False, f"Error de impresora ESC/POS: {e}"
        except Exception as e:
            return False, f"Error general al imprimir factura: {e}"
