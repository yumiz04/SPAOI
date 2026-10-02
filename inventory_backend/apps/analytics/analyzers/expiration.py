from datetime import timedelta

from apps.core.dates import as_of_date
from apps.lots.models import Lot
from apps.products.models import Product
from apps.risk_config.services import RiskConfigService
from .rules import classify_expiration


class ExpirationAnalyzer:
    """Lotes activos con cantidad > 0 y fecha de caducidad (RF-B10/RN-B06)."""

    VERSION = "1.0.0"

    @classmethod
    def run(cls, product_id=None, severity=None, limit=None, within_days=None):
        cfg = RiskConfigService.resolve()
        warning = cfg.expiry_warning_days
        hoy = as_of_date()

        qs = Lot.objects.filter(
            status=Lot.Status.ACTIVO, quantity__gt=0, expiration_date__isnull=False
        )
        if product_id:
            qs = qs.filter(product_id=product_id)
        if within_days is not None:
            qs = qs.filter(expiration_date__lte=hoy + timedelta(days=int(within_days)))
        qs = qs.order_by("expiration_date", "product_id")

        names = dict(Product.objects.values_list("id", "name"))

        out = []
        for lote in qs:
            dias = (lote.expiration_date - hoy).days
            nivel = classify_expiration(dias, warning)
            if severity and nivel != severity:
                continue
            out.append(
                {
                    "lot_id": lote.id,
                    "product_id": lote.product_id,
                    "product_name": names.get(lote.product_id),
                    "lot_number": lote.lot_number,
                    "quantity": lote.quantity,
                    "expiration_date": lote.expiration_date.isoformat(),
                    "severity": nivel,
                    "inputs": {
                        "days_remaining": dias,
                        "expiry_warning_days": warning,
                        "as_of": hoy.isoformat(),
                    },
                }
            )
        out.sort(key=lambda r: (r["inputs"]["days_remaining"], r["product_id"]))
        return out[:limit] if limit else out