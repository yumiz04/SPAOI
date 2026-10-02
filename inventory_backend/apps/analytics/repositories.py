"""Insumos de los analyzers. Todo agregado en SQL para no traer datos a Python
y mantener el numero de consultas constante sin importar cuantos productos haya (P4)."""

from datetime import timedelta

from django.db.models import F, Min, Sum

from apps.core.dates import as_of_date
from apps.inventory.models import ProductInventory
from apps.purchasing.models import ProductVendor, PurchaseOrderDetail
from apps.sales.models import SalesOrderDetail


def stock_by_product() -> dict[int, int]:
    qs = ProductInventory.objects.values("product_id").annotate(t=Sum("quantity"))
    return {r["product_id"]: r["t"] or 0 for r in qs}


def units_sold_by_product(window_days: int) -> dict[int, int]:
    end = as_of_date()
    start = end - timedelta(days=window_days)
    qs = (
        SalesOrderDetail.objects.filter(
            order__order_date__date__gt=start, order__order_date__date__lte=end
        )
        .values("product_id")
        .annotate(u=Sum("order_qty"))
    )
    return {r["product_id"]: r["u"] or 0 for r in qs}


def pending_by_product() -> dict[int, float]:
    """Ordenes de compra pendientes (1) o aprobadas (2) aun no recibidas."""
    qs = (
        PurchaseOrderDetail.objects.filter(order__status__in=[1, 2])
        .annotate(p=F("order_qty") - F("received_qty"))
        .values("product_id")
        .annotate(t=Sum("p"))
    )
    return {r["product_id"]: float(r["t"] or 0) for r in qs if (r["t"] or 0) > 0}


def lead_time_by_product() -> dict[int, int]:
    qs = ProductVendor.objects.values("product_id").annotate(lt=Min("average_lead_time"))
    return {r["product_id"]: r["lt"] for r in qs}


def vendor_limits(product_id: int):
    return (
        ProductVendor.objects.filter(product_id=product_id)
        .order_by("average_lead_time")
        .values(
            "vendor_id",
            "min_order_qty",
            "max_order_qty",
            "standard_price",
            "average_lead_time",
        )
        .first()
    )