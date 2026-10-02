from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.core.dates import as_of_date
from apps.inventory.models import ProductInventory
from .models import Lot


class LotService:
    @staticmethod
    def expiring(within_days: int):
        """Lotes activos cuya caducidad cae dentro de la ventana (RN-B06)."""
        import datetime

        limit = as_of_date() + datetime.timedelta(days=int(within_days))
        return (
            Lot.objects.filter(
                status=Lot.Status.ACTIVO,
                expiration_date__isnull=False,
                expiration_date__lte=limit,
            )
            .order_by("expiration_date", "product_id")
        )

    @staticmethod
    def list(product_id=None, status=None, vence_en_dias=None, limit=100):
        """Lotes filtrados para el agente (RF-B08)."""
        qs = Lot.objects.all()
        if product_id:
            qs = qs.filter(product_id=product_id)
        if status:
            qs = qs.filter(status=status)
        if vence_en_dias is not None:
            import datetime

            limite = as_of_date() + datetime.timedelta(days=int(vence_en_dias))
            qs = qs.filter(expiration_date__isnull=False, expiration_date__lte=limite)
        qs = qs.order_by("expiration_date", "product_id")[:limit]
        return [
            {
                "lot_id": lote.id,
                "product_id": lote.product_id,
                "location_id": lote.location_id,
                "lot_number": lote.lot_number,
                "quantity": lote.quantity,
                "entry_date": lote.entry_date.isoformat(),
                "expiration_date": (
                    lote.expiration_date.isoformat() if lote.expiration_date else None
                ),
                "status": lote.status,
            }
            for lote in qs
        ]

    @staticmethod
    def reconcile(product_id: int):
        """Compara la suma de lotes ACTIVO contra la existencia en productinventory.

        Solo informativo (P4/RN-B03): devuelve la diferencia sin escribir nada.
        """
        stock_lotes = (
            Lot.objects.filter(product_id=product_id, status=Lot.Status.ACTIVO).aggregate(
                total=Coalesce(Sum("quantity"), 0)
            )["total"]
        )
        stock_real = (
            ProductInventory.objects.filter(product_id=product_id).aggregate(
                total=Coalesce(Sum("quantity"), 0)
            )["total"]
        )
        return {
            "product_id": product_id,
            "lots_quantity": stock_lotes,
            "inventory_quantity": stock_real,
            "difference": stock_real - stock_lotes,
        }