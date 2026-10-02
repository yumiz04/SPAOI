from apps.core.dates import as_of_date
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from .. import repositories as repo
from .rules import classify_stockout

ORDER = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}


class StockoutAnalyzer:
    VERSION = "1.0.0"

    @classmethod
    def run(cls, risk_min="MEDIO", product_id=None, limit=None):
        cfg = RiskConfigService.resolve()
        window = cfg.analysis_period_days
        stock, sold = repo.stock_by_product(), repo.units_sold_by_product(window)
        pending, lead = repo.pending_by_product(), repo.lead_time_by_product()
        names = dict(Product.objects.values_list("id", "name"))

        pids = [product_id] if product_id else stock.keys()
        out = []
        for pid in pids:
            d = sold.get(pid, 0) / window
            lt = lead.get(pid, cfg.default_lead_time_days)
            riesgo, cover = classify_stockout(
                stock.get(pid, 0), d, lt, pending.get(pid, 0), cfg.review_period_days
            )
            if ORDER[riesgo] <= ORDER[risk_min]:
                out.append(
                    {
                        "product_id": pid,
                        "product_name": names.get(pid),
                        "risk": riesgo,
                        "inputs": {
                            "stock": stock.get(pid, 0),
                            "pending": pending.get(pid, 0),
                            "daily_demand": round(d, 3),
                            "lead_time_days": lt,
                            "days_of_cover": None if cover is None else round(cover, 1),
                            "window_days": window,
                            "as_of": as_of_date().isoformat(),
                        },
                    }
                )
        out.sort(key=lambda r: (ORDER[r["risk"]], r["inputs"]["days_of_cover"] or 0))
        return out[:limit] if limit else out