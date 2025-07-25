from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uuid
from models import (
    PrintOrderRequest,
    PrintOrderResponse,
    InvoiceRequest,
    InvoiceResponse,
    ConnectivityResponse,
    ApiError,
)
from printer_service import PrinterService

app = FastAPI(
    title="Sistema de Impresión y Facturación",
    description="API para impresión de comandas y facturación de restaurante",
    version="1.0.0",
)

# Configurar CORS - Solo permitir localhost y dominio específico
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://app.salondescomunaltech.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Instancia del servicio de impresión
printer_service = PrinterService()


@app.get("/", response_model=ConnectivityResponse)
async def health_check():
    """Endpoint para verificar conectividad del servidor"""
    return ConnectivityResponse(
        success=True,
        message="Servidor de impresión funcionando correctamente",
        timestamp=datetime.now().isoformat(),
        server_status="online",
    )


@app.get("/api/health", response_model=ConnectivityResponse)
async def api_health_check():
    """Endpoint alternativo para verificar conectividad"""
    return ConnectivityResponse(
        success=True,
        message="API de impresión disponible",
        timestamp=datetime.now().isoformat(),
        server_status="ready",
    )


@app.post("/api/orders/print", response_model=PrintOrderResponse)
async def print_order(request: PrintOrderRequest):
    """Endpoint para imprimir comandas por estación"""
    try:
        # Log inicial
        print(f"\n=== NUEVA ORDEN DE IMPRESIÓN ===")
        print(f"Orden ID: {request.order_id}")
        print(f"Mesa: {request.table_number}")
        print(f"Total de grupos a imprimir: {len(request.print_groups)}")
        
        # Log de cada grupo
        for i, group in enumerate(request.print_groups, 1):
            print(f"Grupo {i}: {group.print_station.name} ({group.print_station.code})")
            print(f"  - Items en este grupo: {len(group.items)}")
            for item in group.items:
                print(f"    * {item.quantity}x {item.menu_item_name}")

        printed_stations = []
        failed_stations = []

        # Convertir request a dict para pasarlo al servicio
        order_data = {
            "order_id": request.order_id,
            "table_number": request.table_number,
            "diners_count": request.diners_count,
            "waiter_name": request.waiter_name,
            "order_notes": request.order_notes,
            "created_at": request.created_at,
            "subtotal": request.subtotal,
            "tax_amount": request.tax_amount,
            "total_amount": request.total_amount,
        }

        # Imprimir en cada estación (CADA GRUPO POR SEPARADO)
        for i, station_group in enumerate(request.print_groups, 1):
            print(f"\n--- Procesando grupo {i}/{len(request.print_groups)} ---")
            print(f"Estación: {station_group.print_station.name}")
            print(f"IP: {station_group.print_station.printer_ip}")
            print(f"Items únicos para esta estación: {len(station_group.items)}")
            
            # Verificar conectividad con la impresora
            if not printer_service.test_printer_connection(
                station_group.print_station.printer_ip
            ):
                print(f"❌ Fallo de conectividad con {station_group.print_station.name}")
                failed_stations.append(station_group.print_station.code)
                continue

            # Intentar imprimir SOLO los items de este grupo específico
            if printer_service.print_order_to_station(station_group, order_data):
                print(f"✅ Impresión exitosa en {station_group.print_station.name}")
                printed_stations.append(station_group.print_station.code)
            else:
                print(f"❌ Fallo de impresión en {station_group.print_station.name}")
                failed_stations.append(station_group.print_station.code)

        # Generar ID único para la impresión
        print_id = str(uuid.uuid4())

        print(f"\n=== RESUMEN DE IMPRESIÓN ===")
        print(f"Estaciones exitosas: {printed_stations}")
        print(f"Estaciones fallidas: {failed_stations}")

        # Determinar el resultado
        if printed_stations and not failed_stations:
            return PrintOrderResponse(
                success=True,
                message=f"Comanda impresa exitosamente en {len(printed_stations)} estación(es)",
                printed_stations=printed_stations,
                print_id=print_id,
            )
        elif printed_stations and failed_stations:
            return PrintOrderResponse(
                success=True,
                message=f"Comanda impresa parcialmente. {len(printed_stations)} exitosas, {len(failed_stations)} fallidas",
                printed_stations=printed_stations,
                failed_stations=failed_stations,
                print_id=print_id,
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": "No se pudo imprimir en ninguna estación",
                    "code": "PRINT_FAILED",
                    "failed_stations": failed_stations,
                },
            )

    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Error interno del servidor: {str(e)}",
                "code": "INTERNAL_ERROR",
            },
        )


@app.post("/api/orders/invoice", response_model=InvoiceResponse)
async def create_invoice(request: InvoiceRequest):
    """Endpoint para generar e imprimir facturas"""
    try:
        # Intentar imprimir la factura
        success, result = printer_service.print_invoice(request)

        if success:
            invoice_id = str(uuid.uuid4())
            return InvoiceResponse(
                success=True,
                message="Factura generada e impresa exitosamente",
                invoice_number=result,
                invoice_id=invoice_id,
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": f"Error al imprimir factura: {result}",
                    "code": "INVOICE_PRINT_FAILED",
                },
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Error interno del servidor: {str(e)}",
                "code": "INTERNAL_ERROR",
            },
        )


@app.get("/api/printer/test/{printer_ip}")
async def test_printer_connectivity(printer_ip: str):
    """Endpoint para probar conectividad con una impresora específica"""
    try:
        is_connected = printer_service.test_printer_connection(printer_ip)

        return {
            "success": True,
            "printer_ip": printer_ip,
            "connected": is_connected,
            "message": "Impresora conectada"
            if is_connected
            else "Impresora no disponible",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Error al probar conectividad: {str(e)}",
                "code": "CONNECTIVITY_TEST_FAILED",
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
