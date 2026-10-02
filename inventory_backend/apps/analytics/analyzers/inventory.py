from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Sum

from apps.core.dates import as_of_date
from apps.inventory.models import ProductInventory
from apps.products.models import ProductSubcategory
from apps.risk_config.services import RiskConfigService
from .. import repositories as repo

UNIT_VALUE = DecimalField(max_digits=19, decimal_places=4)


class InventoryAnalyzer:
    """Totales, dias de inventario y valor por categoria (RF-B11/B12)."""

    VERSION = "1.0.0"

    @classmethod
    def run(cls):
        cfg = RiskConfigService.resolve()
        window = cfg.analysis_period_days

        skus = ProductInventory.objects.values("product_id").distinct().count()
        unidades = ProductInventory.objects.aggregate(t=Sum("quantity"))["t"] or 0
        valor = (
            ProductInventory.objects.aggregate(
                v=Sum(ExpressionWrapper(F("quantity") * F("product__standard_cost"), output_field=UNIT_VALUE))
            )["v"]
            or Decimal("0")
        )

        vendido = sum(repo.units_sold_by_product(window).values())
        demanda_diaria = vendido / window if window else 0

        return {
            "totals": {
                "skus": skus,
                "units": unidades,
                "inventory_value": float(valor),
            },
            "days_of_inventory": round(unidades / demanda_diaria, 1) if demanda_diaria else None,
            "units_sold_in_window": vendido,
            "window_days": window,
            "as_of": as_of_date().isoformat(),
            "by_category": cls.by_category(),
        }

    @classmethod
    def by_category(cls):
        filas = (
            ProductInventory.objects.filter(product__subcategory__isnull=False)
            .values("product__subcategory__category_id")
            .annotate(
                units=Sum("quantity"),
                value=Sum(
                    ExpressionWrapper(
                        F("quantity") * F("product__standard_cost"), output_field=UNIT_VALUE
                    )
                ),
            )
        )
        nombres = dict(
            ProductSubcategory.objects.values_list("category_id", "category__name").distinct()
        )
        out = [
            {
                "category_id": r["product__subcategory__category_id"],
                "category_name": nombres.get(r["product__subcategory__category_id"]),
                "units": r["units"] or 0,
                "value": float(r["value"] or 0),
            }
            for r in filas
        ]
        out.sort(key=lambda b: -b["value"])
        return out