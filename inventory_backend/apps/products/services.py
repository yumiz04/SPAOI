from django.db.models import Q

from apps.core.exceptions import NotFoundError
from .models import Product


class ProductService:
    @staticmethod
    def search(texto=None, categoria=None, limite=50):
        """Búsqueda de productos para el agente (RF-B01)."""
        qs = Product.objects.select_related("subcategory__category")
        if texto:
            qs = qs.filter(Q(name__icontains=texto) | Q(product_number__icontains=texto))
        if categoria:
            qs = qs.filter(subcategory__category_id=categoria)
        qs = qs.order_by("id")[:limite]
        return [
            {
                "product_id": p.id,
                "name": p.name,
                "product_number": p.product_number,
                "category_id": p.subcategory.category_id if p.subcategory else None,
                "reorder_point": p.reorder_point,
                "safety_stock_level": p.safety_stock_level,
            }
            for p in qs
        ]

    @staticmethod
    def get(product_id) -> Product:
        try:
            product_id = int(product_id)
        except (TypeError, ValueError):
            raise NotFoundError("PRODUCT_NOT_FOUND", "Producto no encontrado")

        product = (Product.objects
                   .select_related("subcategory__category")
                   .filter(pk=product_id)
                   .first())
        if product is None:
            raise NotFoundError("PRODUCT_NOT_FOUND", "Producto no encontrado")
        return product