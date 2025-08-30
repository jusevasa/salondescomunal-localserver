from typing import List, Optional, Union
from pydantic import BaseModel
from datetime import datetime


# Tipos base
class PrintStation(BaseModel):
    id: int
    name: str
    code: str
    printer_ip: str


class MenuItemForPrint(BaseModel):
    id: int
    name: str
    price: float
    category_name: str
    print_station_id: int


class SideForPrint(BaseModel):
    id: int
    name: str


class CookingPointForPrint(BaseModel):
    id: int
    name: str


# Modelos para impresión de comandas
class OrderItemForPrint(BaseModel):
    menu_item_id: int
    menu_item_name: str
    quantity: int
    unit_price: float
    subtotal: float
    cooking_point: Optional[CookingPointForPrint] = None
    notes: Optional[str] = None
    sides: List[SideForPrint] = []


class PrintStationGroup(BaseModel):
    print_station: PrintStation
    items: List[OrderItemForPrint]


class PrintOrderRequest(BaseModel):
    order_id: int
    table_number: str
    diners_count: int
    waiter_name: str
    order_notes: Optional[str] = None
    created_at: str
    print_groups: List[PrintStationGroup]
    subtotal: float
    tax_amount: float
    total_amount: float


class PrintOrderResponse(BaseModel):
    success: bool
    message: str
    printed_stations: List[str]
    failed_stations: Optional[List[str]] = None
    print_id: Optional[str] = None


# Modelos para facturación
class OrderItemForInvoice(BaseModel):
    menu_item_id: int
    menu_item_name: str
    quantity: int
    unit_price: float
    subtotal: float
    tax_rate: float
    tax_amount: float
    cooking_point: Optional[CookingPointForPrint] = None
    notes: Optional[str] = None
    sides: List[SideForPrint] = []


class PaymentInfo(BaseModel):
    method: str  # 'cash' | 'card' | 'transfer' | 'mixed'
    payment_method_name: Optional[str] = (
        None  # Nombre del método enviado desde el frontend
    )
    cash_amount: Optional[float] = None
    card_amount: Optional[float] = None
    transfer_amount: Optional[float] = None
    tip_amount: float
    change_amount: float


class RestaurantInfo(BaseModel):
    name: str
    address: str
    phone: str
    tax_id: str


class InvoiceRequest(BaseModel):
    order_id: int
    table_number: str
    diners_count: int
    waiter_name: str
    order_notes: Optional[str] = None
    created_at: str
    items: List[OrderItemForInvoice]
    subtotal: float
    tax_amount: float
    total_amount: float
    tip_amount: float
    grand_total: float
    payment: PaymentInfo
    restaurant_info: Optional[RestaurantInfo] = None
    printer_ip: Optional[str] = None


class InvoiceResponse(BaseModel):
    success: bool
    message: str
    invoice_number: Optional[str] = None
    pdf_url: Optional[str] = None
    invoice_id: Optional[str] = None


# Respuestas estándar
class ApiError(BaseModel):
    success: bool = False
    error: str
    code: str
    details: Optional[dict] = None


class ApiSuccess(BaseModel):
    success: bool = True
    data: Optional[dict] = None
    message: Optional[str] = None


# Modelo para conectividad
class ConnectivityResponse(BaseModel):
    success: bool
    message: str
    timestamp: str
    server_status: str
