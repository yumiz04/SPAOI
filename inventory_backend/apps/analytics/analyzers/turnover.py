from apps.core.dates import as_of_date
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from .. import repositories as repo
from .rules import classify_turnover

ORDER = {"ALTA_ROTACION": 0, "ROTACION_MEDIA": 1, "BAJA_ROTACION": 2, "SIN_MOVIMIENTO": 3}


class TurnoverAnalyzer:
    VERSION = "1.0.0"

    @classmethod
    def run(cls, category=None, limit=None, classification=None, window_days=None):
        cfg = RiskConfigService.resolve()
        window = window_days or cfg.analysis_period_days
        stock, sold = repo.stock_by_product(), repo.units_sold_by_product(window)
        names = dict(Product.objects.values_list("id", "name"))
        low = cfg.low_turnover_threshold
        high = cfg.high_turnover_threshold

        out = []
        for pid, units_stock in stock.items():
            rotacion, valor = classify_turnover(sold.get(pid, 0), units_stock, low, high)
            if classification and rotacion != classification:
                continue
            out.append(
                {
                    "product_id": pid,
                    "product_name": names.get(pid),
                    "classification": rotacion,
                    "turnover": None if valor == float("inf") else round(valor, 3),
                    "inputs": {
                        "units_sold": sold.get(pid, 0),
                        "avg_inventory": units_stock,
                        "window_days": window,
                        "low_threshold": low,
                        "high_threshold": high,
                        "as_of": as_of_date().isoformat(),
                    },
                }
            )
        out.sort(key=lambda r: (ORDER[r["classification"]], r["turnover"] or 0))
        return out[:limit] if limit else out