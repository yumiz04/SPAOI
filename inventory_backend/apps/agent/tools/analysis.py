"""Herramientas analíticas (SRS §11.3): envuelven los analyzers del Paso 12."""

from pydantic import BaseModel, Field

from apps.agent.registry import agent_tool
from apps.analytics.analyzers.expiration import ExpirationAnalyzer
from apps.analytics.analyzers.inventory import InventoryAnalyzer
from apps.analytics.analyzers.overstock import OverstockAnalyzer
from apps.analytics.analyzers.stockout import StockoutAnalyzer
from apps.analytics.analyzers.turnover import TurnoverAnalyzer
from apps.inventory.services import InventoryService


class InventarioIn(BaseModel):
    product_id: int | None = Field(None, description="ID del producto")
    categoria: int | None = Field(None, description="ID de la categoría")


@agent_tool(
    name="analizar_inventario",
    description="Totales de inventario, días de cobertura y valor por categoría.",
    input_model=InventarioIn,
    service="InventoryAnalyzer.run",
    errors=["PRODUCT_NOT_FOUND", "VALIDATION_ERROR"],
)
def analizar_inventario(product_id=None, categoria=None):
    if product_id:
        return InventoryService.by_product(product_id)
    resultado = InventoryAnalyzer.run()
    if categoria:
        resultado["by_category"] = [
            c for c in resultado["by_category"] if c["category_id"] == categoria
        ]
    return resultado


class DesabastoIn(BaseModel):
    riesgo_minimo: str = Field("ALTO", pattern="^(CRITICO|ALTO|MEDIO|BAJO)$")
    product_id: int | None = None
    limite: int = Field(25, ge=1, le=100)


@agent_tool(
    name="analizar_desabasto",
    description="Lista productos con riesgo de desabasto, con las cifras que lo sustentan.",
    input_model=DesabastoIn,
    service="StockoutAnalyzer.run",
    errors=["VALIDATION_ERROR"],
)
def analizar_desabasto(riesgo_minimo="ALTO", product_id=None, limite=25):
    return StockoutAnalyzer.run(risk_min=riesgo_minimo, product_id=product_id, limit=limite)


class CaducidadesIn(BaseModel):
    dias: int | None = Field(None, ge=0, description="Solo lotes que caducan dentro de N días")
    product_id: int | None = None


@agent_tool(
    name="analizar_caducidades",
    description="Lotes próximos a caducar o caducados, ordenados por urgencia.",
    input_model=CaducidadesIn,
    service="ExpirationAnalyzer.run",
    errors=["VALIDATION_ERROR"],
)
def analizar_caducidades(dias=None, product_id=None):
    return ExpirationAnalyzer.run(product_id=product_id, within_days=dias, limit=100)


class SobreInventarioIn(BaseModel):
    categoria: int | None = Field(None, description="ID de la categoría")
    limite: int = Field(50, ge=1, le=100)


@agent_tool(
    name="analizar_sobreinventario",
    description="Productos con exceso de inventario sobre la cobertura objetivo.",
    input_model=SobreInventarioIn,
    service="OverstockAnalyzer.run",
    errors=["VALIDATION_ERROR"],
)
def analizar_sobreinventario(categoria=None, limite=50):
    return OverstockAnalyzer.run(category=categoria, limit=limite)


class RotacionIn(BaseModel):
    clase: str | None = Field(
        None, pattern="^(ALTA_ROTACION|ROTACION_MEDIA|BAJA_ROTACION|SIN_MOVIMIENTO)$"
    )
    ventana_dias: int | None = Field(None, ge=1, le=730)


@agent_tool(
    name="analizar_rotacion",
    description="Clasifica la rotación del inventario por producto.",
    input_model=RotacionIn,
    service="TurnoverAnalyzer.run",
    errors=["VALIDATION_ERROR"],
)
def analizar_rotacion(clase=None, ventana_dias=None):
    return TurnoverAnalyzer.run(classification=clase, window_days=ventana_dias, limit=100)
