from rest_framework import viewsets
from rest_framework.response import Response

from .filters import ProductFilter
from .models import Product
from .serializers import ProductSerializer
from .services import ProductService


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.select_related("subcategory__category").order_by("id")
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    ordering_fields = ["id", "name", "list_price"]
    search_fields = ["name", "product_number"]

    def retrieve(self, request, *args, **kwargs):
        product = ProductService.get(kwargs["pk"])
        return Response(self.get_serializer(product).data)