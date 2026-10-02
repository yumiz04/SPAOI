from apps.core.dates import as_of_date
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from .. import repositories as repo


class OverstockAnalyzer:
    """Sobreinventario: cobertura por encima de la ventana objetivo (RF-B09)."""

    VERSION = "1.0.0"

    @classmethod
    def run(cls, limit=None, category=None):
        cfg = RiskConfigService.resolve()
        window = cfg.analysis_period_days
        objetivo = cfg.overstock_days_of_cover
        stock, sold = repo.stock_by_product(), repo.units_sold_by_product(window)
        names = dict(Product.objects.values_list("id", "name"))
        costos = dict(Product.objects.values_list("id", "standard_cost"))
        en_categoria = None
        if category:
            en_categoria = set(
                Product.objects.filter(subcategory__category_id=category).values_list("id", flat=True)
            )

        out = []
        for pid, units_stock in stock.items():
            if en_categoria is not None and pid not in en_categoria:
                continue
            d = sold.get(pid, 0) / window
            if d <= 0:
                continue  # sin demanda no se puede afirmar sobreinventario
            cover = units_stock / d
            if cover <= objetivo:
                continue
            exceso = units_stock - d * objetivo
            valor = exceso * float(costos.get(pid) or 0)
            out.append(
                {
                    "product_id": pid,
                    "product_name": names.get(pid),
                    "excess_units": round(exceso, 1),
                    "excess_value": round(valor, 2),
                    "inputs": {
                        "stock": units_stock,
                        "daily_demand": round(d, 3),
                        "days_of_cover": round(cover, 1),
                        "overstock_days_of_cover": objetivo,
                        "standard_cost": float(costos.get(pid) or 0),
                        "window_days": window,
                        "as_of": as_of_date().isoformat(),
                    },
                }
            )
        out.sort(key=lambda r: -r["excess_value"])
        return out[:limit] if limit else out