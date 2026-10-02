# Documentación del Backend — Inventory System

API REST en Django/DRF sobre AdventureWorks (PostgreSQL) que cubre consultas de
inventario, analítica, alertas, pronósticos, recomendaciones, tablero y un **catálogo de
herramientas para agentes** (function calling) que solo accede a la lógica vía servicios.

---

## Índice

1. [Estructura del proyecto](#1-estructura-del-proyecto)
2. [Requisitos previos](#2-requisitos-previos)
3. [Instalación paso a paso](#3-instalación-paso-a-paso)
4. [Conceptos transversales](#4-conceptos-transversales)
5. [Endpoints](#5-endpoints)
6. [Catálogo de herramientas del agente](#6-catálogo-de-herramientas-del-agente)

---

## 1. Estructura del proyecto

Repositorio: `inventory_backend/`

```
inventory_backend/
├── manage.py
├── conftest.py                 # Bootstrap de la BD de pruebas (AW sin migraciones)
├── pyproject.toml              # pytest + cobertura
├── .env / .env.example         # Configuración por entorno
├── Dockerfile                  # Imagen de la API
├── docker-compose.yml          # Servicios db + api
├── requirements/
│   ├── base.txt                # Django, DRF, psycopg, pydantic, gunicorn...
│   └── dev.txt                 # pytest, pytest-django, pytest-cov, ruff, black
├── config/
│   ├── urls.py                 # Enrutador raíz (api/…, docs, auth)
│   ├── wsgi.py / asgi.py
│   └── settings/
│       ├── base.py             # Común (apps, DRF, DRF throttling, DB, fechas)
│       ├── development.py      # DEBUG=True
│       ├── test.py             # Hasher rápido + caché local
│       └── production.py       # DEBUG=False
└── apps/
    ├── core/                   # Utilidades transversales
    │   ├── dates.py            # as_of_date(): única fuente de "hoy"
    │   ├── exceptions.py       # AppError/NotFoundError + exception handler
    │   ├── renderers.py        # EnvelopeJSONRenderer {success,data,message}
    │   ├── pagination.py       # StandardPagination
    │   ├── permissions.py      # ReadOnlyOrRole / DeleteRole
    │   └── management/commands/setup_roles.py
    ├── products/               # Catálogo de productos (RF-B01)
    ├── inventory/              # Existencias, ubicaciones y movimientos
    ├── sales/                  # Ventas por producto
    ├── purchasing/             # Compras y proveedores
    ├── lots/                   # Lotes propios (inventory_agent.lotes) + CRUD
    ├── risk_config/            # Parámetros de riesgo por capas (global/categoría/producto)
    ├── analytics/              # Analyzers + registros de análisis (analisis)
    ├── alerts/                 # Alertas propias (alertas) + comando generate_alerts
    ├── forecasting/            # Pronóstico SES (pronosticos)
    ├── recommendations/        # Propuestas reposición/redistribución (nunca órdenes)
    ├── dashboard/              # Resumen consolidado cacheado
    └── agent/                  # Herramientas del agente + ToolLog
        ├── registry.py         # ToolSpec, catálogo y execute()
        ├── tools/              # query / analysis / predictive / decision / alerts
        ├── models.py           # ToolLog (agent_tool_log)
        └── management/commands/purge_tool_logs.py
```

### Flujo de capas

```
Vistas DRF ─► Services / Analyzers ─► Repositories (ORM) ─► PostgreSQL
                    ▲
        apps/agent/tools (JSON Schema) ─► Services
```

- Las **tools** del agente **no** pueden importar `django.db` ni `*.models`; lo verifica
  `tests/test_architecture.py`.
- `registry.execute()` valida con **pydantic** y **nunca** deja escapar una excepción:
  responde `{success, data, message, code?}` y registra la traza en `agent_tool_log`.
- Las tools de decisión (`proponer_*`) devuelven propuestas: **no** crean órdenes ni
  transferencias (regla RN-B04).

### Esquemas de base de datos

- `inventory_agent`: tablas propias (`lotes`, `alertas`, `analisis`, `pronosticos`,
  `configuracion_riesgo`, `agent_tool_log` y las de Django).
- `production`, `sales`, `purchasing`, `person`, `humanresources`: datos de AdventureWorks,
  modelados como `managed=False` (solo lectura).

---

## 2. Requisitos previos

| Componente | Versión sugerida | Notas |
|------------|------------------|-------|
| Python | 3.12+ (probado en 3.12 y 3.14) | `python --version` |
| PostgreSQL | 15+ con dump AdventureWorks | O usar el compose provisto |
| Docker + Compose | opcional | Para BD y/o API |
| PowerShell / bash | — | Ejemplos para Windows PowerShell y Linux |

Dependencias Python (se instalan solas): Django 5.2, DRF, django-filter,
drf-spectacular, simplejwt, psycopg 3, pydantic 2, gunicorn.

---

## 3. Instalación paso a paso

### 3.1. Obtener la base de datos AdventureWorks

**Opción A — Docker (recomendada).** Usa el repositorio de AdventureWorks:

```powershell
cd C:\Servicios_IA\Inventory_System\AdventureWorks-for-Postgres-master
docker compose up -d
# La primera vez importa el dump; espera a que termine.
docker ps    # debe aparecer ...-db-1 en el puerto 5432
```

La base queda accesible en `localhost:5432`, DB `Adventureworks`, usuario `postgres` /
`postgres`.

**Opción B — PostgreSQL propio.** Crea la base `Adventureworks` y carga el dump
(`install.sh`/`install.sql` del repositorio de AdventureWorks). Verifica:

```powershell
psql -h localhost -U postgres -d Adventureworks -c "select count(*) from production.product;"
```

### 3.2. Preparar el entorno Python

```powershell
cd C:\Servicios_IA\Inventory_System\inventory_backend
python -m venv venv
.\venv\Scripts\Activate.ps1            # PowerShell
# En Linux/macOS:  source venv/bin/activate
pip install --upgrade pip
pip install -r requirements/dev.txt
```

> En Linux/macOS sustituye `.\venv\Scripts\python.exe` por `./venv/bin/python`.

### 3.3. Configurar variables de entorno

```powershell
Copy-Item .env.example .env
notepad .env
```

Contenido mínimo de `.env`:

```ini
DJANGO_SECRET_KEY=dev-secret-change-me
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_HOST=localhost
DB_PORT=5432
DB_NAME=Adventureworks
DB_USER=postgres
DB_PASSWORD=postgres
ANALYSIS_AS_OF_DATE=2025-06-29
AGENT_THROTTLE_RATE=120/min
AGENT_TOOL_LOG_RETENTION_DAYS=180
```

> `ANALYSIS_AS_OF_DATE` es la fecha de referencia de **todos** los análisis (ventana de 90
> días por defecto). El dump incluido tiene datos 2022–2025: **no** uses `2014-06-30`.

### 3.4. Migrar y crear datos propios

```powershell
python manage.py migrate            # crea inventory_agent.* (lotes, alertas, etc.)
python manage.py setup_roles        # grupos viewer, analyst, inventory_manager
python manage.py ensure_superuser   # crea/actualiza el admin desde DJANGO_SUPERUSER_*
```

Datos de ejemplo (opcionales pero recomendados para la demo):

```powershell
python manage.py seed_lots                 # lotes con caducidades -20/+10/+30/+90 días
python manage.py generate_alerts           # alertas a partir de los analyzers
python manage.py purge_tool_logs --dry-run # comprueba la política de retención
```

### 3.5. Crear el superusuario y asignar roles

`ensure_superuser` es **idempotente** (crea o actualiza) y toma los datos del entorno:

```ini
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=ADMIN12345
DJANGO_SUPERUSER_EMAIL=admin@example.com
```

```powershell
python manage.py ensure_superuser   # superusuario + los 3 roles
```

Alternativa interactiva (sin rol asignado automáticamente): `python manage.py createsuperuser`.
Para dar roles a otro usuario: añádelo al grupo correspondiente desde el admin
(`/admin/`) o con `user.groups.add(Group.objects.get(name='analyst'))`.

### 3.6. Arrancar el servidor

```powershell
python manage.py runserver 0.0.0.0:8000
```

- API: <http://localhost:8000/api/>
- Swagger UI: <http://localhost:8000/api/docs/>
- OpenAPI: <http://localhost:8000/api/schema/>
- Admin: <http://localhost:8000/admin/>

### 3.7. Ejecución con Docker

```powershell
docker compose up --build
```

Levanta `db` (AdventureWorks) y `api` (aplica `migrate` + `setup_roles` +
`ensure_superuser` y sirve con gunicorn en el puerto 8000). Para reiniciar de cero:
`docker compose down -v`.

### 3.8. Tests y cobertura

```powershell
python -m pytest
python -m pytest --cov=apps --cov-report=term-missing
```

Los modelos de AdventureWorks no tienen migraciones; `conftest.py` los marca como
gestionados durante los tests para que `run_syncdb` cree las tablas en la base de pruebas.
Por eso **no** se usa `--reuse-db`.

---

## 4. Conceptos transversales

### 4.1. Autenticación (JWT)

- `POST /api/auth/token` → respuesta envuelta: los tokens van en `data.access` y
  `data.refresh` (el envelope también aplica a `auth/token`).
- Todas las rutas `/api/*` requieren `Authorization: Bearer <access>`.
- Renueva con `POST /api/auth/refresh` enviando `{ "refresh": "..." }`.

### 4.2. Envelope de respuesta

Salvo las respuestas que ya traen `success`, el renderer envuelve:

```json
{ "success": true, "data": { ... }, "message": null }
```

Error controlado:

```json
{ "success": false, "data": null, "message": "Producto no encontrado", "code": "PRODUCT_NOT_FOUND" }
```

Códigos habituales: `VALIDATION_ERROR` (400), `NOT_AUTHENTICATED` (401),
`PERMISSION_DENIED` (403), `NOT_FOUND` (404), `METHOD_NOT_ALLOWED` (405),
`CONFLICT`/`DUPLICATE_LOT`/`DUPLICATE_ALERT`/`ALERT_ALREADY_CLOSED` (409),
`THROTTLED` (429), `INTERNAL_ERROR` (500).

### 4.3. Paginación y filtros

Listados paginados (`count`, `page`, `page_size`, `next`, `previous`, `results`) con
`page_size` (por defecto 20, máximo 100). Orden con `?ordering=campo` y `-campo`. Los
ViewSets de productos incorporan `?search=`.

### 4.4. Roles

| Rol | Alcance |
|-----|---------|
| `viewer` | Lectura: consultas, analítica, tablero, agente (tools de lectura) |
| `analyst` | Lo anterior + recomendaciones (`POST`) |
| `inventory_manager` | Todo + CRUD de lotes, alertas y tools *mutating* del agente |

El superusuario tiene siempre acceso.

### 4.5. Fechas de análisis

`as_of_date()` = `ANALYSIS_AS_OF_DATE` (o la fecha de hoy si no se define). Los analyzers
usan ventanas relativas a esa fecha, por lo que todas las métricas son reproducibles.

---

## 5. Endpoints

Prefijo común: `/api`. Todas requieren JWT salvo `auth/*`.

### 5.1. Resumen

| Método | Ruta | Roles | Descripción |
|--------|------|-------|-------------|
| GET | `/api/ping` | autenticado | Salud + usuario |
| POST | `/api/auth/token` | anónimo | Obtener tokens |
| POST | `/api/auth/refresh` | anónimo | Renovar token |
| GET | `/api/schema/` · `/api/docs/` | autenticado | OpenAPI / Swagger UI |
| GET | `/api/products` | autenticado | Listado de productos |
| GET | `/api/products/{id}` | autenticado | Producto |
| GET | `/api/inventory` | autenticado | Existencias por producto/ubicación |
| GET | `/api/inventory/{product_id}` | autenticado | Existencias agregadas del producto |
| GET | `/api/movements` | autenticado | Historial de movimientos |
| GET | `/api/locations` | autenticado | Ubicaciones |
| GET | `/api/sales` | autenticado | Ventas por producto |
| GET | `/api/purchases` | autenticado | Compras |
| GET | `/api/suppliers` | autenticado | Proveedores por producto |
| GET/POST | `/api/lots` | lectura: todos · escritura: manager | Lotes |
| GET/PATCH/DELETE | `/api/lots/{id}` | lectura: todos · escritura: manager | Lote (DELETE = baja lógica) |
| GET/PATCH | `/api/risk-config` | lectura: todos · escritura: manager | Parámetros de riesgo |
| GET | `/api/risk-config/layers` | autenticado | Capas configuradas |
| GET | `/api/analytics/stockout` | autenticado | Riesgo de desabasto |
| GET | `/api/analytics/depletion` | autenticado | Agotamiento (lista) |
| GET | `/api/analytics/depletion/{product_id}` | autenticado | Agotamiento (producto) |
| GET | `/api/analytics/turnover` | autenticado | Rotación |
| GET | `/api/analytics/overstock` | autenticado | Sobreinventario |
| GET | `/api/analytics/expiration` | autenticado | Caducidades |
| GET | `/api/analytics/inventory` | autenticado | Totales y valor por categoría |
| GET | `/api/alerts/` | autenticado | Alertas |
| POST | `/api/alerts/` | manager | Crear alerta manual |
| PATCH | `/api/alerts/{id}/` | manager | Cerrar alerta |
| POST | `/api/forecast` | autenticado | Pronóstico SES |
| POST | `/api/recommendations/replenishment` | analyst/manager | Propuesta de reposición |
| POST | `/api/recommendations/redistribution` | analyst/manager | Propuesta de traspasos |
| GET | `/api/dashboard/summary` | autenticado | Resumen del tablero |
| GET | `/api/agent/tools` | autenticado | Catálogo de herramientas |
| POST | `/api/agent/tools/{name}/execute` | lectura: todos · mutating: manager | Ejecutar herramienta |

> `alerts` se registra con `DefaultRouter`, por lo que sus rutas **llevan barra final**
> (`/api/alerts/`). El resto usa `SimpleRouter(trailing_slash=False)` (**sin** barra final).

### 5.2. Consultas de AdventureWorks

**Productos** — `GET /api/products`

Filtros: `product_id`, `name`, `product_number`, `category`, `subcategory`, `search`.
Orden: `id`, `name`, `list_price`.
Respuesta (`data.results[]`): `id`, `name`, `product_number`, `color`, `standard_cost`,
`list_price`, `safety_stock_level`, `reorder_point`, `category`, `subcategory_name`.

**Existencias** — `GET /api/inventory`

Filtros: `product`/`product_id`, `location`/`location_id`, `minimum_quantity`,
`maximum_quantity`. Orden: `quantity`, `product_id`, `location_id`.
Campos: `product_id`, `product_name`, `location_id`, `location_name`, `quantity`,
`shelf`, `bin`.

**Existencias agregadas** — `GET /api/inventory/{product_id}` → total por ubicación.

**Movimientos** — `GET /api/movements`

Filtros: `product`, `date_from`, `date_to`, `type` (`W` trabajo, `S` venta, `P` compra).
Orden: `transaction_date`, `product_id`.

**Ventas** — `GET /api/sales`
Filtros: `product`/`product_id`, `start_date`, `end_date`.
Orden: `order__order_date`, `product_id`, `order_qty`.

**Compras** — `GET /api/purchases`
Filtros: `product`/`product_id`, `vendor`, `status` (1..4), `start_date`, `end_date`.
Orden: `order__order_date`, `product_id`.

**Proveedores** — `GET /api/suppliers?product=<id>` → proveedores ordenados por lead time.

### 5.3. Lotes — `/api/lots`

- `GET /api/lots`: filtros `product`, `location`, `status`
  (`ACTIVO|AGOTADO|CADUCADO|BLOQUEADO|ELIMINADO`), `expiring_within=<días>`, `order`.
  Excluye `ELIMINADO`. Incluye `days_remaining`.
- `POST /api/lots` (manager): `product_id`, `location_id`, `lot_number`, `quantity`,
  `entry_date`, `expiration_date`, `status` (opcional). Duplicado → **409 `DUPLICATE_LOT`**.
- `PATCH /api/lots/{id}` (manager): edición parcial.
- `DELETE /api/lots/{id}` (manager): **baja lógica** (pasa a `ELIMINADO`).

### 5.4. Configuración de riesgo — `/api/risk-config`

- `GET /api/risk-config?product_id=&category_id=` → parámetros **resueltos**
  (precedencia producto > categoría > global > defaults).
- `PATCH /api/risk-config` (manager): hace *upsert* de la capa indicada. Campos:
  `product_id`, `category_id`, `min_stock`, `expiry_warning_days`,
  `overstock_days_of_cover`, `analysis_period_days`, `low_turnover_threshold`,
  `high_turnover_threshold`, `service_level_z`, `review_period_days`,
  `default_lead_time_days`. Responde **201** si creó la capa, **200** si la actualizó.
- `GET /api/risk-config/layers` → todas las capas.

Valores por defecto si no hay configuración: `min_stock=null`, `expiry_warning_days=30`,
`overstock_days_of_cover=180`, `analysis_period_days=90`, `low_turnover_threshold=1.0`,
`high_turnover_threshold=6.0`, `service_level_z=1.65`, `review_period_days=7`,
`default_lead_time_days=14`.

### 5.5. Analítica — `/api/analytics/*`

| Ruta | Parámetros | Devuelve |
|------|-----------|----------|
| `/stockout` | `risk_min` (CRITICO\|ALTO\|MEDIO\|BAJO, def. MEDIO), `product_id`, `limit` | productos en riesgo con sus cifras |
| `/depletion` | `risk_min`, `limit` | fecha estimada de agotamiento |
| `/depletion/{product_id}` | — | agotamiento del producto (o `null` + motivo) |
| `/turnover` | `limit` | clasificación de rotación |
| `/overstock` | `limit` | exceso sobre cobertura objetivo |
| `/expiration` | `product_id`, `severity` (CADUCADO\|ALTO\|MEDIO\|BAJO), `limit` | lotes por urgencia |
| `/inventory` | — | totales, días de inventario y valor por categoría |

Cada ejecución queda registrada en `analisis` (trazabilidad, RN-B05).

### 5.6. Alertas — `/api/alerts/`

- `GET`: filtros `type` (=`alert_type`), `alert_type`, `severity`, `status`, `product_id`.
- `POST` (manager):

```json
{
  "product_id": 680,
  "location_id": null,
  "alert_type": "BAJO_STOCK",
  "severity": "MEDIA",
  "message": "Stock por debajo del mínimo",
  "details": {}
}
```

  Tipos: `DESABASTO, BAJO_STOCK, SOBREINVENTARIO, BAJA_ROTACION, CADUCIDAD_PROXIMA,
  PRODUCTO_CADUCADO, AGOTAMIENTO_ESTIMADO`.
  Severidades: `BAJA, MEDIA, ALTA, CRITICA`. Duplicado pendiente → **409 `DUPLICATE_ALERT`**.

- `PATCH /api/alerts/{id}/` (manager): `{ "status": "ATENDIDA" }` o `"DESCARTADA"`.
  Si ya estaba cerrada → **409 `ALERT_ALREADY_CLOSED`**.
- `DELETE` → **405** (no permitido: las alertas se cierran).

### 5.7. Pronóstico — `POST /api/forecast`

```json
{ "product_id": 680, "historical_days": 365, "forecast_days": 30, "alpha": 0.3 }
```

Devuelve `level`, `sigma`, `confidence`, la serie `forecast[]` y, si hay poco historial,
`warning: "Historial insuficiente"`. Persiste el pronóstico (tabla `pronosticos`).

### 5.8. Recomendaciones

- `POST /api/recommendations/replenishment` — body `{ "product_id": 680 }` o
  `{ "category": 1 }`. Devuelve `is_proposal: true`, `count` y `results[]` con
  `action` (`PROPONER_ORDEN`/`NO_REPONER`), `suggested_quantity`, `justification`, etc.
- `POST /api/recommendations/redistribution` — propone traspasos entre ubicaciones.

Ambas **no** crean órdenes ni transferencias; dejan traza en `analisis`.

### 5.9. Tablero — `GET /api/dashboard/summary`

```json
{
  "total_products": 504,
  "total_inventory": 335974,
  "low_stock_products": 7,
  "stockout_risks": 12,
  "expiring_products": 0,
  "overstock_products": 74,
  "low_turnover_products": 401,
  "pending_alerts": 0
}
```

Cacheado 120 s (`dashboard:summary`). Los valores dependen de `ANALYSIS_AS_OF_DATE` y de
los datos sembrados; `pending_alerts` empieza en 0 hasta ejecutar `generate_alerts`.

### 5.10. Agente — `/api/agent/*`

- `GET /api/agent/tools` → catálogo con `name`, `description`, `input_schema`
  (JSON Schema), `errors` y `mutating`.
- `POST /api/agent/tools/{name}/execute`:

```json
{
  "parameters": { "riesgo_minimo": "ALTO", "limite": 5 },
  "conversation_id": "conv-1",
  "user_request": "¿Qué productos están en riesgo?"
}
```

Respuesta (siempre HTTP 200, también ante error de dominio):

```json
{ "success": true, "data": [ ... ], "message": null }
```

Errores: `{"success": false, "data": null, "message": "...", "code": "VALIDATION_ERROR"}`.
Códigos: `TOOL_NOT_FOUND`, `VALIDATION_ERROR`, `PRODUCT_NOT_FOUND`, `INTERNAL_ERROR`, etc.
Las tools *mutating* (`crear_alerta`, `atender_alerta`) exigen `inventory_manager`
(**403** en otro caso). Limitado a `AGENT_THROTTLE_RATE` (120/min por defecto); al exceder
→ **429 `THROTTLED`**. Cada ejecución se guarda en `agent_tool_log`.

---

## 6. Catálogo de herramientas del agente

19 herramientas organizadas por categoría. Cada una valida su entrada con pydantic.

### Consulta

| Herramienta | Parámetros | Servicio |
|-------------|-----------|----------|
| `buscar_productos` | `texto`, `categoria`, `limite` (≤100) | `ProductService.search` |
| `obtener_existencias` | `product_id`, `location_id` | `InventoryService.list_flat` |
| `obtener_lotes` | `product_id`, `status`, `vence_en_dias` | `LotService.list` |
| `obtener_movimientos` | `product_id`*, `fecha_inicio`, `fecha_fin`, `tipo` (W/S/P) | `MovementService.list` |
| `obtener_ventas` | `product_id`*, `fecha_inicio`, `fecha_fin` | `SalesService.list` |
| `obtener_compras` | `product_id`, `vendor_id`, `estado` (1..4) | `PurchaseService.list` |
| `obtener_proveedores` | `product_id`* | `SupplierService.list` |

### Analítica

| Herramienta | Parámetros | Servicio |
|-------------|-----------|----------|
| `analizar_inventario` | `product_id`, `categoria` | `InventoryAnalyzer.run` |
| `analizar_desabasto` | `riesgo_minimo`, `product_id`, `limite` | `StockoutAnalyzer.run` |
| `analizar_caducidades` | `dias`, `product_id` | `ExpirationAnalyzer.run` |
| `analizar_sobreinventario` | `categoria`, `limite` | `OverstockAnalyzer.run` |
| `analizar_rotacion` | `clase`, `ventana_dias` | `TurnoverAnalyzer.run` |

### Predictiva

| Herramienta | Parámetros | Servicio |
|-------------|-----------|----------|
| `pronosticar_demanda` | `product_id`*, `dias_historicos`, `dias_pronostico` | `ForecastService.forecast` |
| `estimar_fecha_agotamiento` | `product_id`* | `DepletionAnalyzer.run_for_product` |

### Decisión (propuestas, no órdenes)

| Herramienta | Parámetros | Servicio |
|-------------|-----------|----------|
| `proponer_reposicion` | `product_id`, `categoria` | `RecommendationService.replenishment` |
| `proponer_redistribucion` | `product_id`, `categoria` | `RecommendationService.redistribution` |

### Alertas

| Herramienta | Parámetros | Mutating |
|-------------|-----------|----------|
| `obtener_alertas` | `tipo`, `severidad`, `estado` | no |
| `crear_alerta` | `product_id`*, `tipo`*, `severidad`*, `mensaje`*, `location_id` | **sí** |
| `atender_alerta` | `alerta_id`*, `nota` | **sí** |

`*` = obligatorio. `mutating` = requiere rol `inventory_manager`.