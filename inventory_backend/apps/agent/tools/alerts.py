"""Herramientas de alertas (SRS §11.3). ``crear_alerta`` y ``atender_alerta`` son las
únicas con efecto de escritura y solo tocan el esquema propio (RN-B04)."""

from pydantic import BaseModel, Field

from apps.agent.registry import agent_tool
from apps.alerts.services import AlertService

TIPOS = "^(DESABASTO|BAJO_STOCK|SOBREINVENTARIO|BAJA_ROTACION|CADUCIDAD_PROXIMA|PRODUCTO_CADUCADO|AGOTAMIENTO_ESTIMADO)$"
SEVERIDADES = "^(BAJA|MEDIA|ALTA|CRITICA)$"
ESTADOS = "^(PENDIENTE|ATENDIDA|DESCARTADA)$"


class AlertasIn(BaseModel):
    tipo: str | None = Field(None, pattern=TIPOS)
    severidad: str | None = Field(None, pattern=SEVERIDADES)
    estado: str | None = Field(None, pattern=ESTADOS)


@agent_tool(
    name="obtener_alertas",
    description="Lista las alertas filtradas por tipo, severidad o estado.",
    input_model=AlertasIn,
    service="AlertService.list_data",
    errors=["VALIDATION_ERROR"],
)
def obtener_alertas(tipo=None, severidad=None, estado=None):
    return AlertService.list_data({"type": tipo, "severity": severidad, "status": estado})


class CrearAlertaIn(BaseModel):
    product_id: int = Field(..., description="ID del producto (obligatorio)")
    tipo: str = Field(..., pattern=TIPOS, description="Tipo de alerta")
    severidad: str = Field(..., pattern=SEVERIDADES)
    mensaje: str = Field(..., min_length=1)
    location_id: int | None = None


@agent_tool(
    name="crear_alerta",
    description="Crea una alerta manual (solo inventory_manager).",
    input_model=CrearAlertaIn,
    service="AlertService.create",
    mutating=True,
    errors=["DUPLICATE_ALERT", "VALIDATION_ERROR"],
)
def crear_alerta(product_id, tipo, severidad, mensaje, location_id=None):
    alerta = AlertService.create(
        product_id=product_id,
        alert_type=tipo,
        severity=severidad,
        message=mensaje,
        location_id=location_id,
    )
    return AlertService.to_dict(alerta)


class AtenderAlertaIn(BaseModel):
    alerta_id: int = Field(..., description="ID de la alerta (obligatorio)")
    nota: str | None = Field(None, description="Nota de resolución")


@agent_tool(
    name="atender_alerta",
    description="Marca una alerta pendiente como ATENDIDA (solo inventory_manager).",
    input_model=AtenderAlertaIn,
    service="AlertService.update_status",
    mutating=True,
    errors=["ALERT_NOT_FOUND", "ALERT_ALREADY_CLOSED", "VALIDATION_ERROR"],
)
def atender_alerta(alerta_id, nota=None):
    alerta = AlertService.update_status(alerta_id, "ATENDIDA", note=nota)
    return AlertService.to_dict(alerta)
