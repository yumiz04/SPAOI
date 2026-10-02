"""Herramientas de consulta (SRS §11.3): solo lectura de servicios."""

from datetime import date

from pydantic import BaseModel, Field

from apps.agent.registry import agent_tool
from apps.inventory.services import InventoryService, MovementService
from apps.lots.services import LotService
from apps.products.services import ProductService
from apps.purchasing.services import PurchaseService, SupplierService
from apps.sales.services import SalesService


class BuscarProductosIn(BaseModel):
    texto: str | None = Field(None, description="Texto a buscar en nombre o número de producto")
    categoria: int | None = Field(None, description="ID de la categoría")
    limite: int = Field(50, ge=1, le=100, description="Máximo de resultados")


@agent_tool(
    name="buscar_productos",
    description="Busca productos por texto y/o categoría.",
    input_model=BuscarProductosIn,
    service="ProductService.search",
    errors=["VALIDATION_ERROR"],
)
def buscar_productos(texto=None, categoria=None, limite=50):
    return ProductService.search(texto=texto, categoria=categoria, limite=limite)


class ExistenciasIn(BaseModel):
    product_id: int | None = Field(None, description="ID del producto")
    location_id: int | None = Field(None, description="ID de la ubicación")


@agent_tool(
    name="obtener_existencias",
    description="Devuelve las existencias por producto y/o ubicación.",
    input_model=ExistenciasIn,
    service="InventoryService.list_flat",
    errors=["PRODUCT_NOT_FOUND", "VALIDATION_ERROR"],
)
def obtener_existencias(product_id=None, location_id=None):
    return InventoryService.list_flat(product_id=product_id, location_id=location_id, limit=100)


class LotesIn(BaseModel):
    product_id: int | None = Field(None, description="ID del producto")
    status: str | None = Field(None, pattern="^(ACTIVO|AGOTADO|CADUCADO|BLOQUEADO|ELIMINADO)$")
    vence_en_dias: int | None = Field(None, ge=0, description="Solo lotes que vencen dentro de N días")


@agent_tool(
    name="obtener_lotes",
    description="Lista los lotes, opcionalmente por producto y proximidad de caducidad.",
    input_model=LotesIn,
    service="LotService.list",
    errors=["VALIDATION_ERROR"],
)
def obtener_lotes(product_id=None, status=None, vence_en_dias=None):
    return LotService.list(product_id=product_id, status=status, vence_en_dias=vence_en_dias, limit=100)


class MovimientosIn(BaseModel):
    product_id: int = Field(..., description="ID del producto (obligatorio)")
    fecha_inicio: date | None = Field(None, description="Fecha inicial ISO (YYYY-MM-DD)")
    fecha_fin: date | None = Field(None, description="Fecha final ISO (YYYY-MM-DD)")
    tipo: str | None = Field(None, pattern="^[WSP]$", description="W trabajo, S venta, P compra")


@agent_tool(
    name="obtener_movimientos",
    description="Movimientos de inventario de un producto.",
    input_model=MovimientosIn,
    service="MovementService.list",
    errors=["VALIDATION_ERROR"],
)
def obtener_movimientos(product_id, fecha_inicio=None, fecha_fin=None, tipo=None):
    return MovementService.list(
        product_id=product_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, tipo=tipo, limit=100
    )


class VentasIn(BaseModel):
    product_id: int = Field(..., description="ID del producto (obligatorio)")
    fecha_inicio: date | None = Field(None, description="Fecha inicial ISO (YYYY-MM-DD)")
    fecha_fin: date | None = Field(None, description="Fecha final ISO (YYYY-MM-DD)")


@agent_tool(
    name="obtener_ventas",
    description="Ventas de un producto en un rango de fechas.",
    input_model=VentasIn,
    service="SalesService.list",
    errors=["VALIDATION_ERROR"],
)
def obtener_ventas(product_id, fecha_inicio=None, fecha_fin=None):
    return SalesService.list(
        product_id=product_id, fecha_inicio=fecha_inicio, fecha_fin=fecha_fin, limit=100
    )


class ComprasIn(BaseModel):
    product_id: int | None = Field(None, description="ID del producto")
    vendor_id: int | None = Field(None, description="ID del proveedor")
    estado: int | None = Field(None, ge=1, le=4, description="1 Pendiente, 2 Aprobada, 3 Rechazada, 4 Completa")


@agent_tool(
    name="obtener_compras",
    description="Órdenes de compra por producto, proveedor o estado.",
    input_model=ComprasIn,
    service="PurchaseService.list",
    errors=["VALIDATION_ERROR"],
)
def obtener_compras(product_id=None, vendor_id=None, estado=None):
    return PurchaseService.list(product_id=product_id, vendor_id=vendor_id, estado=estado, limit=100)


class ProveedoresIn(BaseModel):
    product_id: int = Field(..., description="ID del producto (obligatorio)")


@agent_tool(
    name="obtener_proveedores",
    description="Proveedores de un producto, ordenados por lead time.",
    input_model=ProveedoresIn,
    service="SupplierService.list",
    errors=["VALIDATION_ERROR"],
)
def obtener_proveedores(product_id):
    return SupplierService.list(product_id=product_id, limit=100)
