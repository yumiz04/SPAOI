# Agente de Inventario — Documentación

Agente conversacional que responde preguntas de inventario usando 19 herramientas
(function calling) contra la API REST del backend Django. Se orquesta en el mismo
`docker-compose` del backend y expone un endpoint HTTP `/chat` para hablar con él
como usuario final.

---

## Índice

1. [Qué es y qué puede hacer](#1-qué-es-y-qué-puede-hacer)
2. [Arquitectura](#2-arquitectura)
3. [Estructura de archivos](#3-estructura-de-archivos)
4. [Variables de entorno](#4-variables-de-entorno)
5. [Las 19 herramientas](#5-las-19-herramientas)
6. [Cómo funciona por dentro](#6-cómo-funciona-por-dentro)
7. [API HTTP](#7-api-http)
8. [Guía de levantamiento con Docker Compose](#8-guía-de-levantamiento-con-docker-compose)
9. [Guía de usuario](#9-guía-de-usuario)
10. [Pruebas](#10-pruebas)
11. [Solución de problemas](#11-solución-de-problemas)
12. [Limitaciones conocidas](#12-limitaciones-conocidas)

---

## 1. Qué es y qué puede hacer

El agente es una capa de **razonamiento** sobre el backend de inventario. No tiene
lógica de negocio propia: todas las reglas de negocio, umbrales y cálculos viven en el
backend (Django + PostgreSQL/AdventureWorks). El agente decide **qué pregunta hacer**,
**con qué argumentos** y **cómo explicar la respuesta**.

Puede:

- Buscar productos por nombre o categoría.
- Consultar existencias, lotes, movimientos, ventas, compras y proveedores.
- Analizar desabasto, sobreinventario, caducidades, rotación y totales.
- Pronosticar demanda y estimar fechas de agotamiento.
- Proponer reposiciones y redistribuciones (recomendaciones, **no ejecutan acciones**).
- Crear y cerrar alertas.

Restricción importante: **nunca inventa datos**. El system prompt lo prohíbe
explícitamente y todas las respuestas se construyen a partir de la salida de las tools.
Si una consulta viene vacía, el agente lo dice en lugar de rellenar.

---

## 2. Arquitectura

```
┌──────────────────────────────────────────────────────────────┐
│  Usuario                                                     │
│  curl / Postman / cualquier cliente HTTP                     │
└───────────────────────────┬──────────────────────────────────┘
                            │  POST /chat  {message, session_id}
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Contenedor "agent"  (python:3.14-slim + uvicorn :8080)     │
│                                                              │
│  api.py ──────────── FastAPI: /chat  /chat/reset  /health    │
│     │                                                        │
│     ▼                                                        │
│  agente.py ─────────── bucle de function calling             │
│     │  ├─ memoria.py ──── SimpleMemory + system prompt       │
│     │  └─ _OP ─────────── mapa nombre → método               │
│            │                                                 │
│            ▼                                                 │
│  tools_inventory.py ── InventoryTools (19 métodos @_safe)    │
│     │        + INVENTORY_TOOLS (19 esquemas JSON)             │
│     └─ requests.Session + JWT (login con reintento en 401)   │
└───────────────────────────┬──────────────────────────────────┘
                            │  HTTP  POST /api/auth/token
                            │         POST /api/agent/tools/<tool>/execute
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Contenedor "api"  (Django + gunicorn :8000)                 │
│  apps/agent  → 19 tools con la lógica de negocio real        │
└───────────────────────────┬──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  Contenedor "db"  (PostgreSQL + AdventureWorks, 504 SKUs)   │
└──────────────────────────────────────────────────────────────┘

Fuera del flujo: OpenCode Zen / OpenAI-compatible
  modelo `space-bunny-free` (configurable con API_OPENCODE_MODEL)
```

El agente **no** se conecta a PostgreSQL en tiempo de ejecución: siempre pasa por la
API. La conexión directa a la base (`INVENTORY_DB_URL`) solo se usa en una prueba de
integración que verifica que el dataset está cargado.

---

## 3. Estructura de archivos

```
agente_inventario/
├── agente.py            # Núcleo: cliente OpenAI, tools, dispatcher y bucle del agente
├── api.py               # API HTTP FastAPI (/chat, /chat/reset, /health)
├── tools_inventory.py   # Las 19 tools: clase InventoryTools + catálogo INVENTORY_TOOLS
├── memoria.py           # SimpleMemory + system prompt
├── memoria_large.py     # (legado, no usado por el agente actual)
├── utils/
│   └── tools_utils.py   # Decorador @_safe: convierte ValueError en {"success": false}
├── tests/
│   ├── conftest.py                  # Fixtures: tools (session) y api (con skip)
│   └── test_inventory_tools.py      # 9 unitarias + 19 de integración
├── e2e_runner.py        # Batería E2E de 19 prompts contra el agente real
├── e2e_report.json      # Salida de la última corrida E2E
├── Dockerfile           # Imagen del agente (uvicorn en :8080)
├── .dockerignore
├── requirements.txt     # Dependencias fijadas por versión
├── requirements-dev.txt # pytest para la suite
├── pytest.ini
└── .env                 # Credenciales (NO versionar, NO imprimir)
```

---

## 4. Variables de entorno

El agente lee el `.env` de su carpeta con `load_dotenv()`. En Docker, el compose las
inyecta desde ese mismo archivo (ver [sección 8](#8-guía-de-levantamiento-con-docker-compose)).

### Proveedor del LLM

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `API_OPENCODE_KEY` | sí | — | API key del proveedor. |
| `API_OPENCODE_URL` | sí | — | Base URL compatible con OpenAI. |
| `API_OPENCODE_MODEL` | sí | — | Nombre del modelo. |
| `API_OPENCODE_MAX_TOKENS` | no | `4000` | Tope de tokens por respuesta. **No lo bajes por debajo de ~2000**: el modelo consume tokens en razonamiento y, si se corta, devuelve `content` vacío y el usuario recibe una respuesta en blanco. |

### Backend de inventario

| Variable | Obligatoria | Default | Descripción |
|---|---|---|---|
| `INVENTORY_API_URL` | no | `http://localhost:8000` | Base de la API. En Docker la sobrescribe el compose a `http://api:8000`. |
| `INVENTORY_API_USER` | no | `admin` | Usuario para el login JWT. Debe tener rol `inventory_manager` si quieres usar `crear_alerta` / `atender_alerta`. |
| `INVENTORY_API_PASSWORD` | no | `ADMIN12345` | Contraseña del usuario. |
| `INVENTORY_DB_URL` | no | `postgresql://postgres:postgres@localhost:5432/Adventureworks` | Solo la usa la prueba `test_postgresql_accesible`. |

### Ejemplo de `.env`

```dotenv
API_OPENCODE_KEY=tu-api-key
API_OPENCODE_URL=https://api.opencode.ai/v1
API_OPENCODE_MODEL=space-bunny-free
API_OPENCODE_MAX_TOKENS=4000

INVENTORY_API_URL=http://localhost:8000
INVENTORY_API_USER=admin
INVENTORY_API_PASSWORD=ADMIN12345
INVENTORY_DB_URL=postgresql://postgres:postgres@localhost:5432/Adventureworks
```

---

## 5. Las 19 herramientas

Cada herramienta tiene dos piezas que deben coincidir:

1. **El método** de `InventoryTools` (`tools_inventory.py`), decorado con `@_safe`, que
   hace la llamada HTTP.
2. **El esquema** en `INVENTORY_TOOLS` (`tools_inventory.py`), en formato JSON de
   function calling de OpenAI, que es lo que lee el modelo para saber qué puede pedir.

Todas pasan por el mismo endpoint genérico del backend:

```
POST /api/agent/tools/<nombre>/execute
Authorization: Bearer <JWT>
Content-Type: application/json

{"parameters": {"product_id": 680, "limite": 10}}
```

El backend responde **siempre con HTTP 200**; el resultado real va en el cuerpo:

```json
{"success": true,  "data": [...], "message": null}
{"success": false, "data": null,  "message": "...", "code": "PRODUCT_NOT_FOUND"}
```

### Resumen

| # | Herramienta | Familia | Obligatorio | Opcionales | ¿Escribe? |
|--:|---|---|---|---|---|
| 1 | `buscar_productos` | Consulta | — | `texto`, `categoria`, `limite` | no |
| 2 | `obtener_existencias` | Consulta | — | `product_id`, `location_id` | no |
| 3 | `obtener_lotes` | Consulta | — | `product_id`, `status`, `vence_en_dias` | no |
| 4 | `obtener_movimientos` | Consulta | `product_id` | `fecha_inicio`, `fecha_fin`, `tipo` | no |
| 5 | `obtener_ventas` | Consulta | `product_id` | `fecha_inicio`, `fecha_fin` | no |
| 6 | `obtener_compras` | Consulta | — | `product_id`, `vendor_id`, `estado` | no |
| 7 | `obtener_proveedores` | Consulta | `product_id` | — | no |
| 8 | `analizar_inventario` | Analítica | — | `product_id`, `categoria` | no |
| 9 | `analizar_desabasto` | Analítica | — | `riesgo_minimo`, `product_id`, `limite` | no |
| 10 | `analizar_caducidades` | Analítica | — | `dias`, `product_id` | no |
| 11 | `analizar_sobreinventario` | Analítica | — | `categoria`, `limite` | no |
| 12 | `analizar_rotacion` | Analítica | — | `clase`, `ventana_dias` | no |
| 13 | `pronosticar_demanda` | Predictiva | `product_id` | `dias_historicos`, `dias_pronostico` | no |
| 14 | `estimar_fecha_agotamiento` | Predictiva | `product_id` | — | no |
| 15 | `proponer_reposicion` | Decisión | — | `product_id`, `categoria` | no (solo propuesta) |
| 16 | `proponer_redistribucion` | Decisión | — | `product_id`, `categoria` | no (solo propuesta) |
| 17 | `obtener_alertas` | Alertas | — | `tipo`, `severidad`, `estado` | no |
| 18 | `crear_alerta` | Alertas | `product_id`, `tipo`, `severidad`, `mensaje` | `location_id` | **sí** |
| 19 | `atender_alerta` | Alertas | `alerta_id` | `nota` | **sí** |

### Catálogos de valores válidos

| Contexto | Valores |
|---|---|
| `obtener_lotes.status` | `ACTIVO`, `AGOTADO`, `CADUCADO`, `BLOQUEADO`, `ELIMINADO` |
| `obtener_movimientos.tipo` | `W` trabajo, `S` venta, `P` compra |
| `obtener_compras.estado` | `1` Pendiente, `2` Aprobada, `3` Rechazada, `4` Completa |
| `analizar_desabasto.riesgo_minimo` | `CRITICO`, `ALTO`, `MEDIO`, `BAJO` (default `ALTO`) |
| `analizar_rotacion.clase` | `ALTA_ROTACION`, `ROTACION_MEDIA`, `BAJA_ROTACION`, `SIN_MOVIMIENTO` |
| `obtener_alertas.tipo` | `DESABASTO`, `BAJO_STOCK`, `SOBREINVENTARIO`, `BAJA_ROTACION`, `CADUCIDAD_PROXIMA`, `PRODUCTO_CADUCADO`, `AGOTAMIENTO_ESTIMADO` |
| `*.severidad` | `BAJA`, `MEDIA`, `ALTA`, `CRITICA` |
| `obtener_alertas.estado` | `PENDIENTE`, `ATENDIDA`, `DESCARTADA` |

### Detalle por herramienta

**Consultas**

- **`buscar_productos`** — Busca por texto (nombre o número de producto) y/o categoría.
  `limite` 1–100, default 50. Útil para resolver un nombre a un `product_id`.
- **`obtener_existencias`** — Existencias por producto y/o ubicación. Devuelve lista.
- **`obtener_lotes`** — Lotes, con filtro de estado y de proximidad de caducidad
  (`vence_en_dias`).
- **`obtener_movimientos`** — Movimientos de un producto. `product_id` es obligatorio
  (no se puede pedir el histórico completo). `tipo` filtra por `W`/`S`/`P`.
- **`obtener_ventas`** — Ventas de un producto en un rango de fechas ISO.
- **`obtener_compras`** — Órdenes de compra por producto, proveedor o estado.
- **`obtener_proveedores`** — Proveedores de un producto, ordenados por lead time.
  Requiere `product_id`.

**Analítica**

- **`analizar_inventario`** — Totales, días de cobertura y valor; por producto o categoría.
- **`analizar_desabasto`** — Productos en riesgo con las cifras que lo sustentan
  (cobertura, demanda diaria, lead time). `limite` default 25.
- **`analizar_caducidades`** — Lotes próximos a caducar o ya caducados, por urgencia.
- **`analizar_sobreinventario`** — Exceso sobre la cobertura objetivo. `limite` default 50.
- **`analizar_rotacion`** — Clasifica la rotación por producto. `ventana_dias` 1–730.

**Predictiva**

- **`pronosticar_demanda`** — Suavizado exponencial simple.
  `dias_historicos` default 90 (1–730), `dias_pronostico` default 30 (1–365).
  Devuelve `data.forecast`.
- **`estimar_fecha_agotamiento`** — Fecha estimada de agotamiento con la demanda reciente.

**Decisión**

- **`proponer_reposicion`** — Cantidades sugeridas con justificación. **No crea órdenes.**
- **`proponer_redistribucion`** — Traspasos sugeridos entre ubicaciones. **No persiste nada.**

**Alertas**

- **`obtener_alertas`** — Filtra por `tipo`, `severidad` y/o `estado`.
- **`crear_alerta`** — Alta manual. Requiere rol `inventory_manager`; con otro rol el
  backend responde `403` y la tool devuelve el error al modelo.
- **`atender_alerta`** — Cierra una alerta como `ATENDIDA`. Mismo requisito de rol.

### Permisos

`crear_alerta` y `atender_alerta` son las únicas que **modifican datos**, y exigen rol
`inventory_manager`. Si el usuario configurado en `.env` no lo tiene, el agente lo
explica en vez de fallar en silencio. Las 17 restantes son de solo lectura.

---

## 6. Cómo funciona por dentro

### El bucle de function calling

`agente.responder(memory, text_user, MAX_TOOL_ROUNDS=8)` hace:

```
for cada ronda (máx. 8):
    1. Agrega el mensaje del usuario a la memoria.
    2. Llama al LLM con [system prompt] + historial + catálogo de 19 tools.
    3. Si la respuesta trae tool_calls:
         a. Guarda el mensaje del asistente con las tool_calls.
         b. Ejecuta cada tool.
         c. Agrega un mensaje role="tool" con el JSON de resultado.
         d. Vuelve a la ronda 2 (el modelo ve el resultado y decide qué hacer).
    4. Si NO trae tool_calls:
         devuelve el texto como respuesta final.
Si se agotan las 8 rondas: "La operacion necesito demasiadas rondas..."
```

Esto significa que una sola pregunta del usuario puede disparar **varias** tools: el
modelo primero consulta, luego con lo que vio pide más detalle, y al final redacta.
Ejemplo real de una sola pregunta:

```
"¿Qué órdenes de compra hay para el producto 680?"
  → obtener_compras, obtener_proveedores, obtener_existencias,
    buscar_productos, analizar_inventario, obtener_lotes,
    analizar_desabasto, obtener_compras(estado=2) ...
  → respuesta consolidada
```

### Memoria

`memoria.SimpleMemory` es una deque de los últimos **20 mensajes** por sesión. El system
prompt se reconstruye en cada llamada e incluye la fecha y hora actuales:

```
Agente de inventario. Usa solo las tools.
Ahora: <fecha y hora local>
No inventes datos. Pide solo argumentos obligatorios. Usa la tool adecuada.
Reporta errores. Sé breve.
Las fechas van en ISO (YYYY-MM-DD). Las propuestas de reposición o redistribución
no ejecutan acciones.
```

La última línea es la que impide que el agente presente una recomendación como si
fuera una orden ya emitida.

### Autenticación

`InventoryTools` mantiene una sesión de `requests` y un token en memoria:

1. En el primer uso hace `POST /api/auth/token` y guarda `data.access`.
2. Cada tool envía `Authorization: Bearer <token>`.
3. Si una tool recibe **401**, descarta el token, vuelve a autenticarse y reintenta **una vez**.
4. Si la API no está alcanzable o no devuelve token, lanza `ValueError`.

El decorador `@_safe` (`utils/tools_utils.py`) atrapa ese `ValueError` y devuelve
`{"success": false, "error": "..."}` en lugar de propagar la excepción. Así el modelo
recibe el error como información y puede explicárselo al usuario en lugar de romper la
conversación.

### Filtro de parámetros

`_execute` descarta los `None` antes de enviar el cuerpo. Por eso una tool con diez
parámetros opcionales solo manda los que el modelo rellenó:

```python
params = {k: v for k, v in parameters.items() if v is not None}
```

---

## 7. API HTTP

Base: `http://localhost:8090` (puerto en el host). Documentación interactiva de FastAPI
en `/docs`.

### `GET /health`

```bash
curl http://localhost:8090/health
```
```json
{"status": "ok"}
```

### `POST /chat`

**Request**

```json
{
  "message": "¿Qué productos tienen riesgo de agotarse?",
  "session_id": "demo"
}
```

| Campo | Tipo | Obligatorio | Default | Descripción |
|---|---|---|---|---|
| `message` | string | sí | — | Mensaje del usuario. Mínimo 1 carácter. |
| `session_id` | string | no | `"default"` | Agrupa conversaciones. El historial se mantiene mientras el servicio viva. |

**Response `200`**

```json
{
  "session_id": "demo",
  "response": "5 productos en riesgo CRÍTICO:\n- **876** Hitch Rack..."
}
```

**Errores**

| Código | Causa |
|---|---|
| `422` | Falta `message` o no cumple el esquema. |
| `400` | `message` vacío o solo espacios. |

> El handler de `def chat` (síncrono) corre en el threadpool de Starlette, así que
> varias peticiones simultáneas se procesan en paralelo. La memoria de una misma
> `session_id` sí es compartida: evita mandar dos mensajes a la vez con el mismo id.

### `POST /chat/reset`

Olvida el historial de una sesión.

```bash
curl -X POST http://localhost:8090/chat/reset \
     -H "Content-Type: application/json" \
     -d '{"session_id":"demo"}'
```
```json
{"session_id": "demo", "status": "reset"}
```

### Ejemplo de conversación con contexto

```bash
# turno 1
curl -X POST http://localhost:8090/chat -H "Content-Type: application/json" \
     -d '{"message":"¿Qué productos tienen riesgo de agotarse?","session_id":"demo"}'

# turno 2 — el agente recuerda la lista del turno 1
curl -X POST http://localhost:8090/chat -H "Content-Type: application/json" \
     -d '{"message":"De esos, ¿cuáles recomiendas reponer primero?","session_id":"demo"}'
```

El segundo turno es el que de verdad valida la memoria: responde "de esos" sin
necesidad de repetir la lista.

### Guía práctica con Insomnia

Insomnia no necesita nada especial para hablar con el agente: es HTTP plano. Lo único
que hay que cuidar es el **timeout**, porque estas peticiones tardan entre 10 y 120
segundos.

#### 1. Crea el environment

`Insomnia → Environments → +` y define:

| Variable | Valor inicial |
|---|---|
| `base_url` | `http://localhost:8090` |
| `session_id` | `insomnia` |

`session_id` es la clave de la memoria. Si lo dejas fijo, todas las peticiones comparten
contexto (útil para probar el seguimiento). Cámbialo cuando quieras empezar de cero.

#### 2. Sube el timeout

Este paso es obligatorio. En los ajustes de la petición, o en
`Settings → Request → Request timeout` (depende de la versión de Insomnia), pon:

```
300000        # milisegundos = 5 minutos
```

Con el valor por defecto (30 s) las peticiones largas fallan aunque el agente esté
funcionando. En Insomnia verás el error como `ETIMEDOUT` o `Error: socket hang up`, no
como un error del agente.

#### 3. Las tres peticiones base

Crea una carpeta `Agente de Inventario` con estas tres peticiones. En Insomnia,
`Method`, `URL`, `Headers` y `Body → raw → JSON`.

**A. Health check** — sin headers, para confirmar que el servicio está arriba

```
GET  {{base_url}}/health
```

Respuesta esperada:

```json
{ "status": "ok" }
```

**B. Chat** — la petición principal

```
POST {{base_url}}/chat
```

Header:

| Key | Value |
|---|---|
| `Content-Type` | `application/json` |

Body (pestaña `Body` → `raw` → selector `JSON`):

```json
{
  "message": "¿Qué productos tienen riesgo de agotarse?",
  "session_id": "{{session_id}}"
}
```

Respuesta `200`:

```json
{
  "session_id": "insomnia",
  "response": "5 productos en riesgo CRÍTICO:\n- **876** Hitch Rack 4-Bike: ..."
}
```

> `response` es **una sola cadena de texto** con los saltos de línea escapados como
> `\n`. Insomnia no renderiza markdown, así que las tablas que devuelve el agente se ven
> como texto con `\n`. Para leerlas bien: activa el formateo JSON de Insomnia y copia el
> valor, o pégalo en un visor de markdown. También puedes pedirle al agente
> "en formato de lista simple" si prefieres texto plano.

**C. Reset de sesión** — para no arrastrar contexto entre pruebas

```
POST {{base_url}}/chat/reset
Content-Type: application/json
```

```json
{ "session_id": "{{session_id}}" }
```

Respuesta:

```json
{ "session_id": "insomnia", "status": "reset" }
```

#### 4. Casos de prueba recomendados

Una petición por herramienta. Copia el `message` en el body de la petición B y dale
`Send`. Esta es la secuencia mínima para un testeo principal:

| # | `message` a pegar | Herramienta esperada |
|--:|---|---|
| 1 | `Dame un panorama general del inventario` | `analizar_inventario` |
| 2 | `¿Qué productos tienen riesgo de agotarse?` | `analizar_desabasto` |
| 3 | `¿Qué productos debería reponer primero?` | `proponer_reposicion` |
| 4 | `¿Qué productos tienen exceso de inventario?` | `analizar_sobreinventario` |
| 5 | `Analiza la rotación del inventario` | `analizar_rotacion` |
| 6 | `¿Qué lotes están próximos a caducar?` | `analizar_caducidades` |
| 7 | `Busca productos que contengan 'Road'` | `buscar_productos` |
| 8 | `¿Cuántas existencias hay del producto 680 y en qué ubicaciones?` | `obtener_existencias` |
| 9 | `Dame los movimientos de inventario del producto 680` | `obtener_movimientos` |
| 10 | `¿Cuáles son las ventas del producto 680?` | `obtener_ventas` |
| 11 | `¿Qué órdenes de compra hay para el producto 680?` | `obtener_compras` |
| 12 | `¿Quiénes son los proveedores del producto 680?` | `obtener_proveedores` |
| 13 | `Pronostica la demanda del producto 680 para los próximos 7 días` | `pronosticar_demanda` |
| 14 | `¿Cuándo se va a agotar el producto 680?` | `estimar_fecha_agotamiento` |
| 15 | `¿Puedo redistribuir inventario del producto 680 entre ubicaciones?` | `proponer_redistribucion` |
| 16 | `Muéstrame las alertas pendientes` | `obtener_alertas` |
| 17 | `Crea una alerta de bajo stock para el producto 680 con severidad MEDIA` | `crear_alerta` ⚠️ escribe |
| 18 | `Marca como ATENDIDA la alerta con id 5` | `atender_alerta` ⚠️ escribe |
| 19 | `Muéstrame los lotes registrados` | `obtener_lotes` |

Las 17 y 18 **modifican la base de datos**. Ejecuta 17 solo si aceptas dejar una alerta
creada, y ajusta el id de 18 al que te devuelva la 17 (o consulta primero con la 16).

Para probar el **contexto**, envía la 2 y luego, sin cambiar `session_id`:

```
De esos, ¿cuáles recomiendas reponer primero y por qué?
```

Si responde "de esos", la memoria funciona. Si responde como si no supiera de qué hablas,
cambiaste el `session_id` o reiniciaste el contenedor.

#### 5. Cómo ver qué tools se ejecutaron

Insomnia solo te muestra la respuesta final. Para ver el razonamiento interno, en otra
terminal:

```bash
cd inventory_backend
docker compose logs -f agent
```

Verás una línea por tool invocada:

```
[ronda 1] analizar_desabasto({"riesgo_minimo": "ALTO", "limite": 25})
```

Es la forma más rápida de confirmar que el agente eligió la herramienta correcta y con
qué argumentos.

#### 6. Tips

- **Acentos:** Insomnia manda el body en UTF-8, así que `¿`, `ñ` y las tildes funcionan
  sin trucos (a diferencia de PowerShell).
- **No lances todo en paralelo:** el backend limita `/api/agent/*` a 120 peticiones por
  minuto. Si compras 20 peticiones y las disparas a la vez, verás errores `THROTTED`.
- **Prueba el body inválido a propósito:** quita `message` y confirma el `422`; pon
  `"message": "   "` y confirma el `400`.
- **Comparte la colección:** `Insomnia → Export` genera un archivo que puedes versionar o
  pasar a otro compañero. Exporta también el environment, que es donde vive `base_url`.
- **Usa la consola si prefieres:** `docker compose logs -f agent` para depurar y
  `.\venv\Scripts\python.exe agente.py` para una sesión conversacional sin HTTP.

---

## 8. Guía de levantamiento con Docker Compose

El agente **no tiene compose propio**: se declara como un servicio dentro del compose
del backend, en `inventory_backend/docker-compose.yml`.

```yaml
  agent:
    build: ../agente_inventario
    env_file:
      - ../agente_inventario/.env
    environment:
      INVENTORY_API_URL: http://api:8000
    depends_on:
      - api
    ports:
      - "8090:8080"
```

Y el servicio `api` necesita admitir el hostname interno del agente:

```yaml
  api:
    environment:
      DJANGO_ALLOWED_HOSTS: localhost,127.0.0.1,api
```

### Requisitos

- Docker Desktop con Compose v2.
- `agente_inventario/.env` con las credenciales del LLM y del backend.
- La imagen `../AdventureWorks-for-Postgres-master` disponible para construir `db`.

### Pasos

```bash
cd inventory_backend
docker compose up -d --build
```

La primera vez tarda varios minutos: compila la imagen del backend y la del agente
(instalando ~45 paquetes Python). Las siguientes son segundos.

### Verificar

```bash
docker compose ps
# los tres servicios "Up": db (healthy), api, agent

curl http://localhost:8090/health
# {"status":"ok"}
```

### Puertos

| Servicio | Host | Contenedor |
|---|---|---|
| `db` | 5432 | 5432 |
| `api` | 8000 | 8000 |
| `agent` | **8090** | 8080 |

> **8090 y no 8080**: en esta máquina el 8080 del host ya lo ocupa Apache, y el compose
> publicaba ahí. El síntoma es un `404` con `Server: Apache` que confunde, porque el
> agente está sano. Si necesitas 8080, libera el puerto de Apache o cambia el mapeo.

### Comandos útiles

```bash
docker compose logs -f agent          # ver las tools que el agente ejecuta (stdout)
docker compose logs --tail 40 api
docker compose restart agent          # reiniciar solo el agente
docker compose up -d --build agent    # reconstruir solo tras cambios de código
docker compose down                   # parar todo (conserva la base)
docker compose down -v                # parar y BORRAR la base
```

Las líneas `[ronda N] obtener_x({...})` que aparecen en los logs son el rastro de qué
tool se llamó y con qué argumentos. Es la forma más rápida de depurar.

### Desarrollo local sin Docker

```bash
cd agente_inventario

# Consola interactiva
.\venv\Scripts\python.exe agente.py

# API HTTP
.\venv\Scripts\python.exe -m uvicorn api:app --port 8080
```

Con `INVENTORY_API_URL=http://localhost:8000` y el backend levantado, todo funciona
igual; la única diferencia es que la API corre en el host y no en la red de Docker.

---

## 9. Guía de usuario

### Cómo preguntar bien

El agente elige las tools por su cuenta; tú no necesitas saber sus nombres. Sí ayuda:

- **Da el `product_id` si lo conoces** (680 = *HL Road Frame - Black, 58*). Ahorra una
  ronda de búsqueda.
- **Da el contexto que quieres**: "en 3 líneas", "solo los críticos", "con el valor en
  dólares". El agente lo respeta.
- **Usa el nombre del producto** si no conoces el id: lo resuelve con `buscar_productos`.
- **Enfócate en una pregunta por mensaje.** El historial es corto (20 mensajes).

### Preguntas que funcionan bien

| Objetivo | Ejemplo de prompt |
|---|---|
| Riesgo de agotamiento | `¿Qué productos tienen riesgo de agotarse?` |
| Prioridad de compra | `¿Qué productos debería reponer primero?` |
| Exceso de stock | `¿Qué productos tienen exceso de inventario?` |
| Rotación | `Analiza la rotación del inventario` |
| Caducidades | `¿Qué lotes están próximos a caducar en 30 días?` |
| Panorama general | `Dame un panorama general del inventario` |
| Existencias | `¿Cuántas existencias hay del producto 680 y en qué ubicaciones?` |
| Compras | `¿Qué órdenes de compra hay para el producto 680?` |
| Proveedores | `¿Quiénes son los proveedores del producto 680?` |
| Pronóstico | `Pronostica la demanda del producto 680 para los próximos 7 días` |
| Agotamiento | `¿Cuándo se va a agotar el producto 680?` |
| Redistribución | `¿Puedo redistribuir inventario del producto 680 entre ubicaciones?` |
| Alertas | `Muéstrame las alertas pendientes` |

### Acciones que sí ejecutan

Estas dos escriben de verdad en la base:

```
Crea una alerta de bajo stock para el producto 680 con severidad MEDIA
Marca como ATENDIDA la alerta con id 5
```

### Preguntas que el agente no puede contestar

- **"Compra las unidades que falten"** — no existe ninguna tool que cree órdenes de
  compra. `proponer_reposicion` solo propone.
- **"Transfiere el stock entre bodegas"** — `proponer_redistribucion` propone, no mueve.
- **"Borra el producto X"** — no hay tool de borrado.
- **"How much is…"** — está en español.

### Qué esperar de las respuestas

- Suelen ser tablas markdown con las cifras y el criterio usado.
- **El agente advierte sobre datos desactualizados**: el dataset tiene fecha de análisis
  `ANALYSIS_AS_OF_DATE` (2025-06-29) y las herramientas la incluyen en la respuesta.
  Si ves un aviso de antigüedad, es correcto, no es un error.
- Cuando una consulta viene vacía, lo dice explícitamente en lugar de inventar.
- Puede detenerse a hacer verificaciones extra antes de responder; es el comportamiento
  deseado.

### Sesiones

- Usa `session_id` para separar conversaciones (por ejemplo, tu usuario, o un cliente).
- Si la respuesta no tiene en cuenta el turno anterior, tu `session_id` cambió o se
  reinició el servicio.
- `POST /chat/reset` para empezar limpio.

---

## 11. Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `404` con `Server: Apache` al pegarle a `/health` | Otro servicio ocupa el 8080 del host. | Usa el puerto **8090**. |
| `No se puede comunicar con el agente (BadRequestError)` | `max_tokens` demasiado bajo: el modelo gasta todo en razonamiento y devuelve contenido vacío o historial inválido. | Sube `API_OPENCODE_MAX_TOKENS` a 4000 o más. |
| Respuesta vacía | mismo motivo que el anterior | Sube `API_OPENCODE_MAX_TOKENS`. |
| `No se pudo conectar con la API` | El backend no está levantado o `INVENTORY_API_URL` es incorrecta. | `docker compose ps`; revisa que sea `http://api:8000` dentro de Docker. |
| `No se pudo autenticar en la API (HTTP 403)` en `crear_alerta` | El usuario no tiene rol `inventory_manager`. | Usa otro usuario en `INVENTORY_API_USER`/`PASSWORD` o asígnale el rol. |
| HTTP `400` desde Django al llamar al agente | `api` no está en `DJANGO_ALLOWED_HOSTS`. | Confirma que el compose lo tenga. |
| El agente no recuerda el turno anterior | Cambió el `session_id`, o se reinició el contenedor (la memoria es en memoria). | Reusa el mismo `session_id`. |
| Muchos `skipped` en pytest | Backend no levantado. | `docker compose up -d`. |
| `La operacion necesito demasiadas rondas` | El modelo no converge en 8 rondas. | Divide la pregunta. |
| `THROTTLED` en la API | Se superó 120 peticiones/min a `/api/agent/*`. | Espera un momento; reduce la frecuencia de preguntas. |

---

## 12. Limitaciones conocidas

- **Memoria en memoria del proceso.** Se pierde al reiniciar el contenedor y no se
  comparte entre réplicas. Con la configuración actual (un solo worker de uvicorn) no hay
  inconsistencias; si se escala horizontalmente hace falta Redis o sesiones persistidas.
- **El historial se repite por ronda.** `responder` agrega el mensaje del usuario al
  entrar a cada ronda, así que en una respuesta de varias rondas el prompt aparece
  repetido en el contexto. No rompe nada, pero gasta tokens.
- **Los datos son de AdventureWorks** con fecha de análisis fija. El agente lo advierte,
  pero conviene tenerlo presente al tomar decisiones.
- **`proponer_reposicion` y `proponer_redistribucion` no ejecutan nada.** Son
  recomendaciones; el agente lo dice explícitamente.
- **Sin streaming.** La respuesta llega completa cuando el modelo termina.
- **Un `product_id` desalineado se propaga.** Si consultas por un id que no existe, las
  tools devuelven vacío y el agente lo reporta; conviene resolver ids con nombres reales.