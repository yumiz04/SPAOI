from dataclasses import asdict, dataclass

from django.core.cache import cache

from .models import RiskConfig

CACHE_PREFIX = "risk-params"
CACHE_TTL = 300


@dataclass(frozen=True)
class RiskParams:
    min_stock: int | None = None
    expiry_warning_days: int = 30
    overstock_days_of_cover: int = 180
    analysis_period_days: int = 90
    low_turnover_threshold: float = 1.0
    high_turnover_threshold: float = 6.0
    service_level_z: float = 1.65
    review_period_days: int = 7
    default_lead_time_days: int = 14

    def to_dict(self):
        return asdict(self)


class RiskConfigService:
    FIELDS = RiskParams.__dataclass_fields__.keys()

    @classmethod
    def _cache_key(cls, product_id, category_id):
        return f"{CACHE_PREFIX}:{product_id or 0}:{category_id or 0}"

    @classmethod
    def resolve(cls, product_id: int | None = None, category_id: int | None = None) -> RiskParams:
        """Precedencia: producto > categoria > global > defaults del codigo."""
        key = cls._cache_key(product_id, category_id)
        cached = cache.get(key)
        if cached is not None:
            return RiskParams(**cached)

        qs = RiskConfig.objects.all()
        layers = [
            qs.filter(product_id=None, category_id=None).first(),
            qs.filter(category_id=category_id, product_id=None).first() if category_id else None,
            qs.filter(product_id=product_id).first() if product_id else None,
        ]
        values = {}
        for layer in layers:  # de menor a mayor prioridad
            if layer:
                for f in cls.FIELDS:
                    v = getattr(layer, f)
                    if v is not None:
                        values[f] = v
        params = RiskParams(
            **{k: (float(v) if k.endswith(("threshold", "_z")) else v) for k, v in values.items()}
        )
        cache.set(key, params.to_dict(), CACHE_TTL)
        return params

    @classmethod
    def invalidate(cls):
        """Se llama al guardar configuracion para que el siguiente resolve no sirva stale."""
        for layer in RiskConfig.objects.all():
            cls.invalidate_for(layer.product_id, layer.category_id)
        cls.invalidate_for(None, None)

    @classmethod
    def invalidate_for(cls, product_id=None, category_id=None):
        cache.delete(cls._cache_key(product_id, category_id))