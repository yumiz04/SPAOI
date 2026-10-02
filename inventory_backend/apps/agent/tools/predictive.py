"""Herramientas predictivas (SRS §11.3): pronóstico SES y fecha de agotamiento."""

from pydantic import BaseModel, Field

from apps.agent.registry import agent_tool
from apps.analytics.analyzers.depletion import DepletionAnalyzer
from apps.forecasting.services import ForecastService


class PronosticoIn(BaseModel):
    product_id: int = Field(..., description="ID del producto (obligatorio)")
    dias_historicos: int = Field(90, ge=1, le=730, description="Días de historia a considerar")
    dias_pronostico: int = Field(30, ge=1, le=365, description="Días a pronosticar")


@agent_tool(
    name="pronosticar_demanda",
    description="Pronostica la demanda diaria de un producto con suavizado exponencial simple.",
    input_model=PronosticoIn,
    service="ForecastService.forecast",
    errors=["PRODUCT_NOT_FOUND", "VALIDATION_ERROR"],
)
def pronosticar_demanda(product_id, dias_historicos=90, dias_pronostico=30):
    resultado = ForecastService.forecast(
        product_id=product_id, historical_days=dias_historicos, forecast_days=dias_pronostico
    )
    ForecastService.persist_analysis(resultado)
    return resultado


class AgotamientoIn(BaseModel):
    product_id: int = Field(..., description="ID del producto (obligatorio)")


@agent_tool(
    name="estimar_fecha_agotamiento",
    description="Estima cuándo se agotará un producto con la demanda reciente.",
    input_model=AgotamientoIn,
    service="DepletionAnalyzer.run_for_product",
    errors=["PRODUCT_NOT_FOUND", "VALIDATION_ERROR"],
)
def estimar_fecha_agotamiento(product_id):
    return DepletionAnalyzer.run_for_product(product_id)
