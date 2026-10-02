from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets

from apps.core.exceptions import AppError
from .filters import InventoryFilter, MovementFilter
from .models import Location, ProductInventory, TransactionHistory
from .serializers import InventoryRowSerializer, LocationSerializer, MovementSerializer
from .services import InventoryService


class InventoryListView(ListAPIView):
    queryset = ProductInventory.objects.select_related("product", "location").order_by("product_id", "location_id")
    serializer_class = InventoryRowSerializer
    filterset_class = InventoryFilter
    ordering_fields = ["quantity", "product_id", "location_id"]


class InventoryByProductView(APIView):
    @extend_schema(
        summary="Existencias agregadas de un producto",
        responses={200: OpenApiTypes.OBJECT},
        tags=["inventory"],
    )
    def get(self, request, product_id: int):
        return Response(InventoryService.by_product(product_id))


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all().order_by("id")
    serializer_class = LocationSerializer


class MovementListView(ListAPIView):
    serializer_class = MovementSerializer
    filterset_class = MovementFilter
    ordering_fields = ["transaction_date", "product_id"]

    def get_queryset(self):
        qs = (
            TransactionHistory.objects
            .select_related("product")
            .order_by("transaction_date", "id")
        )
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")
        if date_from and date_to and date_from > date_to:
            raise AppError("INVALID_DATE_RANGE", "La fecha inicial es posterior a la final", 400)
        return qs
