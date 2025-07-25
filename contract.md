// ============================================================================
// CONTRATOS PARA EL BACKEND - SISTEMA DE IMPRESIÓN Y FACTURACIÓN
// ============================================================================

// Tipos base para el backend
export interface PrintStation {
  id: number
  name: string
  code: string
  printer_ip: string
}

export interface MenuItemForPrint {
  id: number
  name: string
  price: number
  category_name: string
  print_station_id: number
}

export interface SideForPrint {
  id: number
  name: string
}

export interface CookingPointForPrint {
  id: number
  name: string
}

// ============================================================================
// CONTRATO PARA IMPRESIÓN DE COMANDAS
// ============================================================================

export interface OrderItemForPrint {
  menu_item_id: number
  menu_item_name: string
  quantity: number
  unit_price: number
  subtotal: number
  cooking_point?: CookingPointForPrint
  notes?: string
  sides: SideForPrint[]
}

export interface PrintStationGroup {
  print_station: PrintStation
  items: OrderItemForPrint[]
}

export interface PrintOrderRequest {
  // Información de la orden
  order_id: number
  table_number: string
  diners_count: number
  waiter_name: string
  order_notes?: string
  created_at: string
  
  // Items agrupados por estación de impresión
  print_groups: PrintStationGroup[]
  
  // Totales para referencia
  subtotal: number
  tax_amount: number
  total_amount: number
}

export interface PrintOrderResponse {
  success: boolean
  message: string
  printed_stations: string[] // Códigos de las estaciones donde se imprimió
  failed_stations?: string[] // Estaciones que fallaron
  print_id?: string // ID único de la impresión para tracking
}

// ============================================================================
// CONTRATO PARA FACTURACIÓN
// ============================================================================

export interface OrderItemForInvoice {
  menu_item_id: number
  menu_item_name: string
  quantity: number
  unit_price: number
  subtotal: number
  tax_rate: number
  tax_amount: number
  cooking_point?: CookingPointForPrint
  notes?: string
  sides: SideForPrint[]
}

export interface PaymentInfo {
  method: 'cash' | 'card' | 'transfer' | 'mixed'
  cash_amount?: number
  card_amount?: number
  transfer_amount?: number
  tip_amount: number
  change_amount: number
}

export interface InvoiceRequest {
  // Información de la orden
  order_id: number
  table_number: string
  diners_count: number
  waiter_name: string
  order_notes?: string
  created_at: string
  
  // Items completos para facturación
  items: OrderItemForInvoice[]
  
  // Totales calculados
  subtotal: number
  tax_amount: number
  total_amount: number
  tip_amount: number
  grand_total: number
  
  // Información de pago
  payment: PaymentInfo
  
  // Información del restaurante (opcional, puede estar en el backend)
  restaurant_info?: {
    name: string
    address: string
    phone: string
    tax_id: string
  }
}

export interface InvoiceResponse {
  success: boolean
  message: string
  invoice_number?: string
  pdf_url?: string // URL del PDF generado
  invoice_id?: string // ID único de la factura
}

// ============================================================================
// CONTRATOS PARA OPERACIONES ADICIONALES
// ============================================================================

// Reimpresión de comanda
export interface ReprintOrderRequest {
  order_id: number
  print_station_codes?: string[] // Si no se especifica, reimprime en todas
  reason: string
}

// Cancelación de items
export interface CancelItemsRequest {
  order_id: number
  item_ids: number[]
  reason: string
  cancelled_by: string
}

// Facturación parcial
export interface PartialInvoiceRequest extends Omit<InvoiceRequest, 'items'> {
  selected_item_ids: number[]
}

// ============================================================================
// TIPOS DE RESPUESTA ESTÁNDAR
// ============================================================================

export interface ApiError {
  success: false
  error: string
  code: string
  details?: any
}

export interface ApiSuccess<T = any> {
  success: true
  data: T
  message?: string
}

export type ApiResponse<T = any> = ApiSuccess<T> | ApiError

// ============================================================================
// EJEMPLOS DE USO
// ============================================================================

/*
EJEMPLO DE CUERPO PARA IMPRESIÓN DE COMANDA:

POST /api/orders/print
{
  "order_id": 123,
  "table_number": "5",
  "diners_count": 4,
  "waiter_name": "Juan Pérez",
  "order_notes": "Cliente alérgico a mariscos",
  "created_at": "2024-01-15T14:30:00Z",
  "print_groups": [
    {
      "print_station": {
        "id": 1,
        "name": "Cocina Caliente",
        "code": "HOT_KITCHEN",
        "printer_ip": "192.168.1.100"
      },
      "items": [
        {
          "menu_item_id": 15,
          "menu_item_name": "Lomo de Res",
          "quantity": 2,
          "unit_price": 45000,
          "subtotal": 90000,
          "cooking_point": {
            "id": 2,
            "name": "Término Medio"
          },
          "notes": "Sin sal",
          "sides": [
            { "id": 1, "name": "Papas Fritas" },
            { "id": 3, "name": "Ensalada Verde" }
          ]
        }
      ]
    },
    {
      "print_station": {
        "id": 2,
        "name": "Bar",
        "code": "BAR",
        "printer_ip": "192.168.1.101"
      },
      "items": [
        {
          "menu_item_id": 45,
          "menu_item_name": "Mojito",
          "quantity": 3,
          "unit_price": 15000,
          "subtotal": 45000,
          "notes": "Extra menta",
          "sides": []
        }
      ]
    }
  ],
  "subtotal": 135000,
  "tax_amount": 25650,
  "total_amount": 160650
}

EJEMPLO DE CUERPO PARA FACTURACIÓN:

POST /api/orders/invoice
{
  "order_id": 123,
  "table_number": "5",
  "diners_count": 4,
  "waiter_name": "Juan Pérez",
  "created_at": "2024-01-15T14:30:00Z",
  "items": [
    {
      "menu_item_id": 15,
      "menu_item_name": "Lomo de Res",
      "quantity": 2,
      "unit_price": 45000,
      "subtotal": 90000,
      "tax_rate": 0.19,
      "tax_amount": 17100,
      "cooking_point": {
        "id": 2,
        "name": "Término Medio"
      },
      "sides": [
        { "id": 1, "name": "Papas Fritas" },
        { "id": 3, "name": "Ensalada Verde" }
      ]
    }
  ],
  "subtotal": 135000,
  "tax_amount": 25650,
  "total_amount": 160650,
  "tip_amount": 16000,
  "grand_total": 176650,
  "payment": {
    "method": "mixed",
    "cash_amount": 100000,
    "card_amount": 76650,
    "tip_amount": 16000,
    "change_amount": 0
  }
}
*/