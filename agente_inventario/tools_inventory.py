import os

import requests
from dotenv import load_dotenv

from utils.tools_utils import _safe

load_dotenv()

LOTES_STATUS = ["ACTIVO", "AGOTADO", "CADUCADO", "BLOQUEADO", "ELIMINADO"]
RIESGOS = ["CRITICO", "ALTO", "MEDIO", "BAJO"]
ROTACIONES = ["ALTA_ROTACION", "ROTACION_MEDIA", "BAJA_ROTACION", "SIN_MOVIMIENTO"]
ALERT_TIPOS = [
    "DESABASTO",
    "BAJO_STOCK",
    "SOBREINVENTARIO",
    "BAJA_ROTACION",
    "CADUCIDAD_PROXIMA",
    "PRODUCTO_CADUCADO",
    "AGOTAMIENTO_ESTIMADO",
]
SEVERIDADES = ["BAJA", "MEDIA", "ALTA", "CRITICA"]
ESTADOS_ALERTA = ["PENDIENTE", "ATENDIDA", "DESCARTADA"]


class InventoryTools:
    """Herramientas de inventario (SRS RF-25) conectadas a la API REST del backend.

    La API usa PostgreSQL (AdventureWorks) como fuente de datos. Cada método llama al
    endpoint genérico ``/api/agent/tools/<name>/execute`` con JWT, de modo que la lógica
    de negocio vive en un solo lugar (el backend) y aquí solo se expone al agente.
    """

    def __init__(self, base_url: str | None = None, username: str | None = None,
                 password: str | None = None, timeout: int = 30):
        self.base_url = (
            base_url or os.getenv("INVENTORY_API_URL", "http://localhost:8000")
        ).rstrip("/")
        self.username = username or os.getenv("INVENTORY_API_USER", "admin")
        self.password = password or os.getenv("INVENTORY_API_PASSWORD", "ADMIN12345")
        self.timeout = timeout
        self.session = requests.Session()
        self._access = None

    # ------------------------------------------------------------------
    # Infraestructura HTTP
    # ------------------------------------------------------------------
    def _login(self) -> str:
        """Obtiene un token JWT. La respuesta viene envuelta: data.access."""

        try:
            response = self.session.post(
                f"{self.base_url}/api/auth/token",
                json={"username": self.username, "password": self.password},
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise ValueError(f"No se pudo conectar con la API ({error}).")

        if response.status_code >= 400:
            raise ValueError(
                f"No se pudo autenticar en la API (HTTP {response.status_code})."
            )

        token = (response.json().get("data") or {}).get("access")
        if not token:
            raise ValueError("La API no devolvió token de acceso.")

        self._access = token
        return token

    def _headers(self) -> dict:
        if not self._access:
            self._login()
        return {"Authorization": f"Bearer {self._access}"}

    def _execute(self, name: str, **parameters):
        """Llama a la herramienta `name` del backend descartando parámetros nulos."""

        params = {key: value for key, value in parameters.items() if value is not None}
        url = f"{self.base_url}/api/agent/tools/{name}/execute"

        response = self._post(url, params)

        if response.status_code == 401:
            self._access = None
            response = self._post(url, params)

        if response.status_code >= 400:
            raise ValueError(
                f"La API respondió HTTP {response.status_code} al ejecutar '{name}'."
            )

        return response.json()

    def _post(self, url: str, params: dict):
        try:
            return self.session.post(
                url,
                json={"parameters": params},
                headers=self._headers(),
                timeout=self.timeout,
            )
        except requests.RequestException as error:
            raise ValueError(f"No se pudo conectar con la API ({error}).")

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    @_safe
    def buscar_productos(self, texto=None, categoria=None, limite=50):
        #? Busca productos por texto y/o categoría.
        return self._execute("buscar_productos", texto=texto, categoria=categoria, limite=limite)

    @_safe
    def obtener_existencias(self, product_id=None, location_id=None):
        #? Devuelve las existencias por producto y/o ubicación.
        return self._execute("obtener_existencias", product_id=product_id, location_id=location_id)

    @_safe
    def obtener_lotes(self, product_id=None, status=None, vence_en_dias=None):
        #? Lista los lotes, opcionalmente por producto y proximidad de caducidad.
        return self._execute(
            "obtener_lotes",
            product_id=product_id,
            status=status,
            vence_en_dias=vence_en_dias,
        )

    @_safe
    def obtener_movimientos(self, product_id, fecha_inicio=None, fecha_fin=None, tipo=None):
        #? Movimientos de inventario de un producto.
        return self._execute(
            "obtener_movimientos",
            product_id=product_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
        )

    @_safe
    def obtener_ventas(self, product_id, fecha_inicio=None, fecha_fin=None):
        #? Ventas de un producto en un rango de fechas.
        return self._execute(
            "obtener_ventas",
            product_id=product_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

    @_safe
    def obtener_compras(self, product_id=None, vendor_id=None, estado=None):
        #? Órdenes de compra por producto, proveedor o estado.
        return self._execute(
            "obtener_compras", product_id=product_id, vendor_id=vendor_id, estado=estado
        )

    @_safe
    def obtener_proveedores(self, product_id):
        #? Proveedores de un producto, ordenados por lead time.
        return self._execute("obtener_proveedores", product_id=product_id)

    # ------------------------------------------------------------------
    # Analítica
    # ------------------------------------------------------------------
    @_safe
    def analizar_inventario(self, product_id=None, categoria=None):
        #? Totales de inventario, días de cobertura y valor por categoría.
        return self._execute("analizar_inventario", product_id=product_id, categoria=categoria)

    @_safe
    def analizar_desabasto(self, riesgo_minimo="ALTO", product_id=None, limite=25):
        #? Lista productos con riesgo de desabasto, con las cifras que lo sustentan.
        return self._execute(
            "analizar_desabasto",
            riesgo_minimo=riesgo_minimo,
            product_id=product_id,
            limite=limite,
        )

    @_safe
    def analizar_caducidades(self, dias=None, product_id=None):
        #? Lotes próximos a caducar o caducados, ordenados por urgencia.
        return self._execute("analizar_caducidades", dias=dias, product_id=product_id)

    @_safe
    def analizar_sobreinventario(self, categoria=None, limite=50):
        #? Productos con exceso de inventario sobre la cobertura objetivo.
        return self._execute("analizar_sobreinventario", categoria=categoria, limite=limite)

    @_safe
    def analizar_rotacion(self, clase=None, ventana_dias=None):
        #? Clasifica la rotación del inventario por producto.
        return self._execute("analizar_rotacion", clase=clase, ventana_dias=ventana_dias)

    # ------------------------------------------------------------------
    # Predictiva
    # ------------------------------------------------------------------
    @_safe
    def pronosticar_demanda(self, product_id, dias_historicos=90, dias_pronostico=30):
        #? Pronostica la demanda diaria con suavizado exponencial simple.
        return self._execute(
            "pronosticar_demanda",
            product_id=product_id,
            dias_historicos=dias_historicos,
            dias_pronostico=dias_pronostico,
        )

    @_safe
    def estimar_fecha_agotamiento(self, product_id):
        #? Estima cuándo se agotará un producto con la demanda reciente.
        return self._execute("estimar_fecha_agotamiento", product_id=product_id)

    # ------------------------------------------------------------------
    # Decisión (propuestas, nunca órdenes)
    # ------------------------------------------------------------------
    @_safe
    def proponer_reposicion(self, product_id=None, categoria=None):
        #? Propone cantidades de reposición justificadas; no crea órdenes.
        return self._execute("proponer_reposicion", product_id=product_id, categoria=categoria)

    @_safe
    def proponer_redistribucion(self, product_id=None, categoria=None):
        #? Propone traspasos entre ubicaciones; no persiste transferencias.
        return self._execute("proponer_redistribucion", product_id=product_id, categoria=categoria)

    # ------------------------------------------------------------------
    # Alertas
    # ------------------------------------------------------------------
    @_safe
    def obtener_alertas(self, tipo=None, severidad=None, estado=None):
        #? Lista las alertas filtradas por tipo, severidad o estado.
        return self._execute("obtener_alertas", tipo=tipo, severidad=severidad, estado=estado)

    @_safe
    def crear_alerta(self, product_id, tipo, severidad, mensaje, location_id=None):
        #? Crea una alerta manual (solo inventory_manager).
        return self._execute(
            "crear_alerta",
            product_id=product_id,
            tipo=tipo,
            severidad=severidad,
            mensaje=mensaje,
            location_id=location_id,
        )

    @_safe
    def atender_alerta(self, alerta_id, nota=None):
        #? Marca una alerta pendiente como ATENDIDA (solo inventory_manager).
        return self._execute("atender_alerta", alerta_id=alerta_id, nota=nota)


INVENTORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_productos",
            "description": "Busca productos por texto y/o categoría.",
            "parameters": {
                "type": "object",
                "properties": {
                    "texto": {
                        "type": "string",
                        "description": "Texto a buscar en nombre o número de producto.",
                    },
                    "categoria": {
                        "type": "integer",
                        "description": "ID de la categoría.",
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Máximo de resultados (1-100). Por defecto 50.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_existencias",
            "description": "Devuelve las existencias por producto y/o ubicación.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "location_id": {"type": "integer", "description": "ID de la ubicación."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_lotes",
            "description": "Lista los lotes, opcionalmente por producto y proximidad de caducidad.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "status": {
                        "type": "string",
                        "enum": LOTES_STATUS,
                        "description": "Estado del lote.",
                    },
                    "vence_en_dias": {
                        "type": "integer",
                        "description": "Solo lotes que vencen dentro de N días.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_movimientos",
            "description": "Movimientos de inventario de un producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto (obligatorio)."},
                    "fecha_inicio": {"type": "string", "description": "Fecha inicial ISO (YYYY-MM-DD)."},
                    "fecha_fin": {"type": "string", "description": "Fecha final ISO (YYYY-MM-DD)."},
                    "tipo": {
                        "type": "string",
                        "enum": ["W", "S", "P"],
                        "description": "W trabajo, S venta, P compra.",
                    },
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_ventas",
            "description": "Ventas de un producto en un rango de fechas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto (obligatorio)."},
                    "fecha_inicio": {"type": "string", "description": "Fecha inicial ISO (YYYY-MM-DD)."},
                    "fecha_fin": {"type": "string", "description": "Fecha final ISO (YYYY-MM-DD)."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_compras",
            "description": "Órdenes de compra por producto, proveedor o estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "vendor_id": {"type": "integer", "description": "ID del proveedor."},
                    "estado": {
                        "type": "integer",
                        "description": "1 Pendiente, 2 Aprobada, 3 Rechazada, 4 Completa.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_proveedores",
            "description": "Proveedores de un producto, ordenados por lead time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto (obligatorio)."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_inventario",
            "description": "Totales de inventario, días de cobertura y valor por categoría.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "categoria": {"type": "integer", "description": "ID de la categoría."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_desabasto",
            "description": "Lista productos con riesgo de desabasto, con las cifras que lo sustentan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "riesgo_minimo": {
                        "type": "string",
                        "enum": RIESGOS,
                        "description": "Riesgo mínimo a listar. Por defecto ALTO.",
                    },
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "limite": {"type": "integer", "description": "Máximo de resultados (1-100)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_caducidades",
            "description": "Lotes próximos a caducar o caducados, ordenados por urgencia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dias": {"type": "integer", "description": "Solo lotes que caducan dentro de N días."},
                    "product_id": {"type": "integer", "description": "ID del producto."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_sobreinventario",
            "description": "Productos con exceso de inventario sobre la cobertura objetivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "categoria": {"type": "integer", "description": "ID de la categoría."},
                    "limite": {"type": "integer", "description": "Máximo de resultados (1-100)."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "analizar_rotacion",
            "description": "Clasifica la rotación del inventario por producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "clase": {
                        "type": "string",
                        "enum": ROTACIONES,
                        "description": "Clasificación a filtrar.",
                    },
                    "ventana_dias": {
                        "type": "integer",
                        "description": "Ventana de análisis en días (1-730).",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "pronosticar_demanda",
            "description": "Pronostica la demanda diaria de un producto con suavizado exponencial simple.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto (obligatorio)."},
                    "dias_historicos": {
                        "type": "integer",
                        "description": "Días de historia a considerar (1-730). Por defecto 90.",
                    },
                    "dias_pronostico": {
                        "type": "integer",
                        "description": "Días a pronosticar (1-365). Por defecto 30.",
                    },
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "estimar_fecha_agotamiento",
            "description": "Estima cuándo se agotará un producto con la demanda reciente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto (obligatorio)."},
                },
                "required": ["product_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "proponer_reposicion",
            "description": "Propone cantidades de reposición justificadas; no crea órdenes de compra.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "categoria": {"type": "integer", "description": "ID de la categoría."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "proponer_redistribucion",
            "description": "Propone traspasos entre ubicaciones; no persiste transferencias.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto."},
                    "categoria": {"type": "integer", "description": "ID de la categoría."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "obtener_alertas",
            "description": "Lista las alertas filtradas por tipo, severidad o estado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {"type": "string", "enum": ALERT_TIPOS, "description": "Tipo de alerta."},
                    "severidad": {
                        "type": "string",
                        "enum": SEVERIDADES,
                        "description": "Severidad de la alerta.",
                    },
                    "estado": {
                        "type": "string",
                        "enum": ESTADOS_ALERTA,
                        "description": "Estado de la alerta.",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_alerta",
            "description": "Crea una alerta manual (solo inventory_manager).",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "integer", "description": "ID del producto (obligatorio)."},
                    "tipo": {"type": "string", "enum": ALERT_TIPOS, "description": "Tipo de alerta."},
                    "severidad": {"type": "string", "enum": SEVERIDADES, "description": "Severidad."},
                    "mensaje": {"type": "string", "description": "Mensaje de la alerta."},
                    "location_id": {"type": "integer", "description": "ID de la ubicación (opcional)."},
                },
                "required": ["product_id", "tipo", "severidad", "mensaje"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "atender_alerta",
            "description": "Marca una alerta pendiente como ATENDIDA (solo inventory_manager).",
            "parameters": {
                "type": "object",
                "properties": {
                    "alerta_id": {"type": "integer", "description": "ID de la alerta (obligatorio)."},
                    "nota": {"type": "string", "description": "Nota de resolución."},
                },
                "required": ["alerta_id"],
            },
        },
    },
]
