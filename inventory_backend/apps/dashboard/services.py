from django.core.cache import cache

from apps.alerts.models import Alert
from apps.analytics import repositories as repo
from apps.analytics.analyzers.expiration import ExpirationAnalyzer
from apps.analytics.analyzers.overstock import OverstockAnalyzer
from apps.analytics.analyzers.stockout import StockoutAnalyzer
from apps.analytics.analyzers.turnover import TurnoverAnalyzer
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService

CACHE_KEY = "dashboard:summary"
CACHE_TTL = 120

LOW_TURNOVER = ("BAJA_ROTACION", "SIN_MOVIMIENTO")
EXPIRING = ("ALTO", "MEDIO")


class DashboardService:
    """Resumen consolidado (RF-B18). Cacheado 120 s: los analyzers son costosos
    y el tablero se consulta con frecuencia."""

    @staticmethod
    def _low_stock(stock, min_stock):
        reorder = dict(Product.objects.values_list("id", "reorder_point"))
        total = 0
        for pid, unidades in stock.items():
            umbrales = [t for t in (min_stock, reorder.get(pid) or 0) if t]
            if umbrales and unidades < min(umbrales):
                total += 1
        return total

    @staticmethod
    def compute():
        cfg = RiskConfigService.resolve()
        stock = repo.stock_by_product()
        stockout_riesgos = StockoutAnalyzer.run(risk_min="ALTO")
        caducidades = ExpirationAnalyzer.run()
        rotacion = TurnoverAnalyzer.run()

        return {
            "total_products": Product.objects.count(),
            "total_inventory": sum(stock.values()),
            "low_stock_products": DashboardService._low_stock(stock, cfg.min_stock or 0),
            "stockout_risks": len(stockout_riesgos),
            "expiring_products": len(
                {r["product_id"] for r in caducidades if r["severity"] in EXPIRING}
            ),
            "overstock_products": len(OverstockAnalyzer.run()),
            "low_turnover_products": len(
                [r for r in rotacion if r["classification"] in LOW_TURNOVER]
            ),
            "pending_alerts": Alert.objects.filter(status=Alert.Status.PENDIENTE).count(),
        }

    @staticmethod
    def summary():
        return cache.get_or_set(CACHE_KEY, DashboardService.compute, timeout=CACHE_TTL)

    @staticmethod
    def invalidate():
        cache.delete(CACHE_KEY)
