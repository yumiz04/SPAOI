from datetime import timedelta

from apps.core.dates import as_of_date
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from .. import repositories as repo
from .rules import depletion_days

ORDER = {"CRITICO": 0, "ALTO": 1, "MEDIO": 2, "BAJO": 3}


def _risk_from_cover(cover: float) -> str:
    if cover <= 0:
        return "CRITICO"
    if cover <= 7:
        return "ALTO"
    if cover <= 30:
        return "MEDIO"
    return "BAJO"


class DepletionAnalyzer:
    VERSION = "1.0.0"

    @classmethod
    def run(cls, risk_min="MEDIO", product_id=None, limit=None):
        cfg = RiskConfigService.resolve()
        window = cfg.analysis_period_days
        stock, sold = repo.stock_by_product(), repo.units_sold_by_product(window)
        pending = repo.pending_by_product()
        names = dict(Product.objects.values_list("id", "name"))
        hoy = as_of_date()

        pids = [product_id] if product_id else stock.keys()
        out = []
        for pid in pids:
            d = sold.get(pid, 0) / window
            dias = depletion_days(stock.get(pid, 0), d)
            if dias is None:
                # Sin demanda no hay fecha estimada: se omite en vez de inventarla (RN-B03).
                continue
            cover = stock.get(pid, 0) / d
            riesgo = _risk_from_cover(cover)
            if ORDER[riesgo] > ORDER[risk_min]:
                continue
            out.append(
                {
                    "product_id": pid,
                    "product_name": names.get(pid),
                    "risk": riesgo,
                    "estimated_depletion_date": (hoy + timedelta(days=dias)).isoformat(),
                    "inputs": {
                        "stock": stock.get(pid, 0),
                        "daily_demand": round(d, 3),
                        "pending": pending.get(pid, 0),
                        "days_of_cover": round(cover, 1),
                        "depletion_days": dias,
                        "window_days": window,
                        "as_of": hoy.isoformat(),
                    },
                }
            )
        out.sort(key=lambda r: (ORDER[r["risk"]], r["inputs"]["depletion_days"]))
        return out[:limit] if limit else out

    @classmethod
    def run_for_product(cls, product_id: int):
        """Respuesta puntual: fecha estimada o null con el motivo (endpoint por producto)."""
        cfg = RiskConfigService.resolve()
        window = cfg.analysis_period_days
        stock = repo.stock_by_product().get(product_id, 0)
        sold = repo.units_sold_by_product(window).get(product_id, 0)
        d = sold / window
        dias = depletion_days(stock, d)
        nombre = Product.objects.filter(pk=product_id).values_list("name", flat=True).first()

        base = {
            "product_id": product_id,
            "product_name": nombre,
            "stock": stock,
            "window_days": window,
            "as_of": as_of_date().isoformat(),
        }
        if dias is None:
            return {
                **base,
                "daily_demand": 0,
                "estimated_depletion_date": None,
                "message": (
                    "Sin demanda en la ventana de analisis: no se puede estimar el agotamiento"
                ),
            }
        return {
            **base,
            "daily_demand": round(d, 3),
            "days_of_cover": round(stock / d, 1),
            "depletion_days": dias,
            "estimated_depletion_date": (
                as_of_date() + timedelta(days=dias)
            ).isoformat(),
        }