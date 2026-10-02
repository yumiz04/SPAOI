"""Herramientas de decisión (SRS §11.3): propuestas, nunca órdenes ni transferencias (RN-B04)."""

from pydantic import BaseModel, Field

from apps.agent.registry import agent_tool
from apps.recommendations.services import RecommendationService


class PropuestaIn(BaseModel):
    product_id: int | None = Field(None, description="ID del producto")
    categoria: int | None = Field(None, description="ID de la categoría")


@agent_tool(
    name="proponer_reposicion",
    description="Propone cantidades de reposición justificadas; no crea órdenes de compra.",
    input_model=PropuestaIn,
    service="RecommendationService.replenishment",
    errors=["PRODUCT_NOT_FOUND", "VALIDATION_ERROR"],
)
def proponer_reposicion(product_id=None, categoria=None):
    return RecommendationService.replenishment(product_id=product_id, category=categoria)


@agent_tool(
    name="proponer_redistribucion",
    description="Propone traspasos entre ubicaciones; no persiste transferencias.",
    input_model=PropuestaIn,
    service="RecommendationService.redistribution",
    errors=["PRODUCT_NOT_FOUND", "VALIDATION_ERROR"],
)
def proponer_redistribucion(product_id=None, categoria=None):
    return RecommendationService.redistribution(product_id=product_id, category=categoria)
