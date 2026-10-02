from datetime import timedelta

from django.db import transaction

from apps.analytics.models import AnalysisRecord
from apps.core.dates import as_of_date
from apps.core.exceptions import NotFoundError
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from . import repositories as repo
from .rules import propose_transfers, replenishment_qty

PROPOSAL_VERSION = "1.0.0"


class RecommendationService:
    """Propuestas de reposición y redistribución (RF-B16/B17).

    Las tools de decisión NO crean órdenes de compra ni transferencias (RN-B04): solo
    devuelven la propuesta con las cifras que la justifican. Sí se deja traza en
    ``analisis`` (RN-B05), que vive en el esquema propio y no toca AdventureWorks.
    """

    @staticmethod
    def _products(product_id=None, category=None):
        qs = Product.objects.all()
        if product_id:
            qs = qs.filter(pk=product_id)
        if category:
            qs = qs.filter(subcategory__category_id=category)
        return qs

    @staticmethod
    def _ensure_product(product_id):
        if product_id and not Product.objects.filter(pk=product_id).exists():
            raise NotFoundError("PRODUCT_NOT_FOUND", "Producto no encontrado")

    @staticmethod
    def replenishment(product_id=None, category=None):
        RecommendationService._ensure_product(product_id)
        cfg = RiskConfigService.resolve(product_id=product_id)
        window = cfg.analysis_period_days
        stock = repo.stock_by_product()
        pending = repo.pending_by_product()
        lead = repo.lead_time_by_product()
        stats = repo.demand_stats(window)

        productos = list(
            RecommendationService._products(product_id, category).values(
                "id", "name", "safety_stock_level", "reorder_point"
            )
        )
        vendors = repo.preferred_vendors([p["id"] for p in productos])

        hoy = as_of_date()
        resultados = []
        for p in productos:
            pid = p["id"]
            demanda = stats.get(pid, {})
            d = demanda.get("mean", 0.0)
            sd = demanda.get("sd", 0.0)
            lt = lead.get(pid, cfg.default_lead_time_days)
            prov = vendors.get(pid) or {}
            safety = max(p["safety_stock_level"] or 0, cfg.service_level_z * sd * (lt ** 0.5))

            qty = replenishment_qty(
                stock.get(pid, 0),
                pending.get(pid, 0),
                d,
                lt,
                cfg.review_period_days,
                safety,
                prov.get("min_order_qty"),
                prov.get("max_order_qty"),
            )
            resultados.append(
                {
                    "product_id": pid,
                    "product_name": p["name"],
                    "action": qty["action"],
                    "suggested_quantity": qty["suggested"],
                    "suggested_vendor_id": prov.get("vendor_id"),
                    "expected_arrival": (hoy + timedelta(days=lt)).isoformat(),
                    "is_proposal": True,
                    "justification": {
                        "stock": stock.get(pid, 0),
                        "pending": pending.get(pid, 0),
                        "daily_demand": round(d, 3),
                        "daily_demand_sd": round(sd, 3),
                        "lead_time_days": lt,
                        "review_period_days": cfg.review_period_days,
                        "safety_stock": round(safety, 1),
                        "min_order_qty": prov.get("min_order_qty"),
                        "max_order_qty": prov.get("max_order_qty"),
                        "target_stock": qty["target_stock"],
                        "remaining_need": qty["remaining_need"],
                        "window_days": window,
                        "as_of": hoy.isoformat(),
                    },
                }
            )
        resultados.sort(key=lambda r: (-r["suggested_quantity"], r["product_id"]))
        RecommendationService._persist("replenishment", product_id, category, resultados)
        return resultados

    @staticmethod
    def redistribution(product_id=None, category=None):
        RecommendationService._ensure_product(product_id)
        cfg = RiskConfigService.resolve(product_id=product_id)
        window = cfg.analysis_period_days
        stats = repo.demand_stats(window)
        lead = repo.lead_time_by_product()
        by_loc = repo.stock_by_product_location()
        nombres = dict(
            RecommendationService._products(product_id, category).values_list("id", "name")
        )

        resultados = []
        for pid, locations in by_loc.items():
            if pid not in nombres:
                continue
            d = stats.get(pid, {}).get("mean", 0.0)
            lt = lead.get(pid, cfg.default_lead_time_days)
            max_cover = cfg.overstock_days_of_cover
            transfers = propose_transfers(locations, d, lt, max_cover)
            propuesta = {
                "product_id": pid,
                "product_name": nombres[pid],
                "is_proposal": True,
                "daily_demand": round(d, 3),
                "min_cover_days": lt,
                "max_cover_days": max_cover,
                "transfers": [
                    {
                        "from_location": t["from_location"],
                        "to_location": t["to_location"],
                        "quantity": t["quantity"],
                        "reason": RecommendationService._transfer_reason(
                            locations, d, lt, max_cover, t
                        ),
                    }
                    for t in transfers
                ],
            }
            if transfers or product_id:
                resultados.append(propuesta)
        resultados.sort(key=lambda r: r["product_id"])
        RecommendationService._persist("redistribution", product_id, category, resultados)
        return resultados

    @staticmethod
    def _transfer_reason(locations, daily_demand, min_cover, max_cover, transfer):
        origen = locations.get(transfer["from_location"], 0)
        destino = locations.get(transfer["to_location"], 0)
        return {
            "origin_stock": origen,
            "destination_stock": destino,
            "origin_cover_days": round(origen / daily_demand, 1) if daily_demand else None,
            "destination_cover_days": round(destino / daily_demand, 1) if daily_demand else None,
            "min_cover_days": min_cover,
            "max_cover_days": max_cover,
        }

    @staticmethod
    @transaction.atomic
    def _persist(analysis_type, product_id, category, resultados):
        AnalysisRecord.objects.create(
            analysis_type=analysis_type,
            product_id=product_id,
            parameters={"category": category},
            result={"count": len(resultados), "proposals": resultados},
            algorithm_version=PROPOSAL_VERSION,
        )
