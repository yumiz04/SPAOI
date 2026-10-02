from django.db.models import Sum
from apps.core.exceptions import NotFoundError
from apps.products.models import Product
from .models import ProductInventory, TransactionHistory


class InventoryService:
    @staticmethod
    def list_flat(product_id=None, location_id=None, limit=100):
        """Existencias aplanadas por producto/ubicación (RF-B02)."""
        qs = ProductInventory.objects.select_related("product", "location")
        if product_id:
            qs = qs.filter(product_id=product_id)
        if location_id:
            qs = qs.filter(location_id=location_id)
        qs = qs.order_by("product_id", "location_id")[:limit]
        return [
            {
                "product_id": r.product_id,
                "product_name": r.product.name,
                "location_id": r.location_id,
                "location_name": r.location.name,
                "quantity": r.quantity,
            }
            for r in qs
        ]

    @staticmethod
    def by_product(product_id: int) -> dict:
        product = Product.objects.filter(pk=product_id).first()
        if not product:
            raise NotFoundError("PRODUCT_NOT_FOUND", "Producto no encontrado")
        rows = (ProductInventory.objects.filter(product_id=product_id)
                .select_related("location")
                .order_by("location_id"))
        locations = [{"location_id": r.location_id, "location_name": r.location.name,
                      "quantity": r.quantity} for r in rows]
        return {"product_id": product.id, "product_name": product.name,
                "total_quantity": sum(l["quantity"] for l in locations), "locations": locations}

    @staticmethod
    def stock_totals() -> dict[int, int]:
        """{product_id: stock total} en una sola consulta agregada."""
        qs = ProductInventory.objects.values("product_id").annotate(total=Sum("quantity"))
        return {r["product_id"]: r["total"] for r in qs}


class MovementService:
    @staticmethod
    def list(product_id, fecha_inicio=None, fecha_fin=None, tipo=None, limit=100):
        """Movimientos de un producto (RF-B04). ``tipo``: W trabajo, S venta, P compra."""
        qs = TransactionHistory.objects.filter(product_id=product_id)
        if fecha_inicio:
            qs = qs.filter(transaction_date__date__gte=fecha_inicio)
        if fecha_fin:
            qs = qs.filter(transaction_date__date__lte=fecha_fin)
        if tipo:
            qs = qs.filter(transaction_type=tipo)
        qs = qs.order_by("-transaction_date", "-id")[:limit]
        return [
            {
                "id": r.id,
                "product_id": r.product_id,
                "transaction_type": r.transaction_type,
                "quantity": r.quantity,
                "actual_cost": float(r.actual_cost),
                "transaction_date": r.transaction_date.isoformat(),
                "reference_order_id": r.reference_order_id,
            }
            for r in qs
        ]
