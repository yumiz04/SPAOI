"""Agregaciones de ventas. Todo en SQL para no traer el detalle a Python (P4)."""

from datetime import date

from django.db.models import Sum
from django.db.models.functions import TruncDate

from .models import SalesOrderDetail


class SalesService:
    @staticmethod
    def daily_units(product_id: int, start: date, end: date) -> dict[date, int]:
        """Unidades vendidas por día para un producto en el rango [start, end]."""
        qs = (
            SalesOrderDetail.objects.filter(
                product_id=product_id,
                order__order_date__date__gte=start,
                order__order_date__date__lte=end,
            )
            .annotate(dia=TruncDate("order__order_date"))
            .values("dia")
            .annotate(u=Sum("order_qty"))
            .order_by("dia")
        )
        return {r["dia"]: r["u"] or 0 for r in qs}

    @staticmethod
    def list(product_id, fecha_inicio=None, fecha_fin=None, limit=100):
        """Ventas de un producto (RF-B06)."""
        qs = SalesOrderDetail.objects.filter(product_id=product_id).select_related("order")
        if fecha_inicio:
            qs = qs.filter(order__order_date__date__gte=fecha_inicio)
        if fecha_fin:
            qs = qs.filter(order__order_date__date__lte=fecha_fin)
        qs = qs.order_by("-order__order_date")[:limit]
        return [
            {
                "order_id": r.order_id,
                "order_date": r.order.order_date.isoformat(),
                "status": r.order.status,
                "order_qty": r.order_qty,
                "unit_price": float(r.unit_price),
            }
            for r in qs
        ]