# Sistema de Impresión y Facturación

Este proyecto implementa un servidor local con Python y FastAPI para manejar la impresión de comandas y facturación de restaurantes usando impresoras térmicas ESC/POS.

## Características

- ✅ Soporte completo para caracteres especiales (ñ, tildes)
- ✅ Impresión de comandas por estaciones
- ✅ Generación e impresión de facturas
- ✅ API REST con documentación automática
- ✅ Contenedorización con Docker
- ✅ Puerto 8080 expuesto

## Endpoints Disponibles

### 1. Conectividad
- `GET /` - Verificar estado del servidor
- `GET /api/health` - Verificar estado de la API
- `GET /api/printer/test/{printer_ip}` - Probar conectividad con impresora

### 2. Impresión de Comandas
- `POST /api/orders/print` - Imprimir comanda por estaciones

### 3. Facturación
- `POST /api/orders/invoice` - Generar e imprimir factura

## Instalación y Uso

### Con Docker (Recomendado)

```bash
# Construir y ejecutar
docker-compose up --build

# Solo ejecutar (después del primer build)
docker-compose up
```

### Sin Docker

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python main.py
```

## Acceso

- **Servidor**: http://localhost:8080
- **Documentación API**: http://localhost:8080/docs
- **Esquema OpenAPI**: http://localhost:8080/redoc

## Configuración de Impresoras

Las impresoras deben estar configuradas en la red local y ser accesibles por IP. El puerto por defecto es 9100 (estándar para impresoras térmicas).

## Ejemplos de Uso

### Probar Conectividad
```bash
curl http://localhost:8080/
```

### Imprimir Comanda
```bash
curl -X POST http://localhost:8080/api/orders/print \
  -H "Content-Type: application/json" \
  -d @ejemplo_comanda.json
```

### Generar Factura
```bash
curl -X POST http://localhost:8080/api/orders/invoice \
  -H "Content-Type: application/json" \
  -d @ejemplo_factura.json
```

## Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **python-escpos**: Librería para impresoras ESC/POS
- **Docker**: Contenedorización
- **Pydantic**: Validación de datos
- **Uvicorn**: Servidor ASGI

## Notas Técnicas

- Codificación CP858 para soporte de caracteres especiales
- Formato de impresión optimizado para tickets de 80mm
- Manejo de errores robusto
- Logs detallados para debugging