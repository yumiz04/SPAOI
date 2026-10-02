"""Insumos agregados de reposición/redistribución. Reutiliza el repositorio de
analytics para stock, pendientes y lead time, y añade lo específico del paso."""

from datetime import timedelta

from django.db.models import Sum

from apps.analytics import repositories as analytics_repo
from apps.core.dates import as_of_date
from apps.inventory.models import ProductInventory
from apps.purchasing.models import ProductVendor
from apps.sales.models import SalesOrderDetail

stock_by_product = analytics_repo.stock_by_product
pending_by_product = analytics_repo.pending_by_product
lead_time_by_product = analytics_repo.lead_time_by_product


def demand_stats(window_days: int) -> dict[int, dict]:
    """Media y desviación estándar de la demanda diaria por producto.

    Una sola consulta: unidades agregadas por (producto, día). Los días sin venta
    aportan 0 y se contemplan con el divisor ``window_days`` al calcular la varianza.
    """
    end = as_of_date()
    start = end - timedelta(days=window_days)
    filas = (
        SalesOrderDetail.objects.filter(
            order__order_date__date__gt=start, order__order_date__date__lte=end
        )
        .values("product_id", "order__order_date__date")
        .annotate(u=Sum("order_qty"))
    )
    acumulado: dict[int, tuple] = {}
    for r in filas:
        pid = r["product_id"]
        u = r["u"] or 0
        total, sumsq = acumulado.get(pid, (0, 0))
        acumulado[pid] = (total + u, sumsq + u * u)

    stats = {}
    for pid, (total, sumsq) in acumulado.items():
        mean = total / window_days
        var = max(0.0, sumsq / window_days - mean * mean)
        stats[pid] = {"mean": mean, "sd": var ** 0.5, "total": total}
    return stats


def stock_by_product_location() -> dict[int, dict[int, int]]:
    """{product_id: {location_id: cantidad}} en una consulta."""
    qs = ProductInventory.objects.values("product_id", "location_id").annotate(t=Sum("quantity"))
    out: dict[int, dict[int, int]] = {}
    for r in qs:
        out.setdefault(r["product_id"], {})[r["location_id"]] = r["t"] or 0
    return out


def preferred_vendors(product_ids=None) -> dict[int, dict]:
    """Proveedor preferido por producto: el de menor ``average_lead_time``.

    Se ordena por (producto, lead time) y se conserva la primera fila de cada
    producto, en una sola consulta (P4).
    """
    qs = ProductVendor.objects.order_by("product_id", "average_lead_time")
    if product_ids is not None:
        qs = qs.filter(product_id__in=list(product_ids))
    qs = qs.values(
        "product_id", "vendor_id", "min_order_qty", "max_order_qty", "average_lead_time"
    )
    out: dict[int, dict] = {}
    for r in qs:
        out.setdefault(r["product_id"], r)
    return out
