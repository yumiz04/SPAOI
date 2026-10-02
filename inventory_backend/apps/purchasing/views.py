from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import AppError
from apps.purchasing.filters import PurchaseFilter
from apps.purchasing.models import ProductVendor, PurchaseOrderDetail
from apps.purchasing.serializers import PurchaseRowSerializer


class PurchaseListView(ListAPIView):
    serializer_class = PurchaseRowSerializer
    filterset_class = PurchaseFilter
    ordering_fields = ["order__order_date", "product_id"]

    def get_queryset(self):
        qs = (
            PurchaseOrderDetail.objects
            .select_related("order", "order__vendor", "product")
            .order_by("order__order_date", "order_id", "detail_id")
        )
        start = self.request.query_params.get("start_date")
        end = self.request.query_params.get("end_date")
        if start and end and start > end:
            raise AppError("INVALID_DATE_RANGE", "La fecha inicial es posterior a la final", 400)
        return qs


class SupplierListView(APIView):
    @extend_schema(
        summary="Proveedores por producto (ordenados por lead time)",
        responses={200: OpenApiTypes.OBJECT},
        tags=["purchasing"],
    )
    def get(self, request, *args, **kwargs):
        product_id = request.query_params.get("product")
        if product_id:
            qs = (
                ProductVendor.objects
                .filter(product_id=product_id)
                .select_related("vendor")
                .order_by("average_lead_time")
            )
        else:
            qs = (
                ProductVendor.objects
                .select_related("vendor")
                .order_by("product_id", "average_lead_time")
            )[:100]

        data = []
        for pv in qs:
            data.append({
                "product_id": pv.product_id,
                "vendor_id": pv.vendor_id,
                "vendor_name": pv.vendor.name,
                "average_lead_time": pv.average_lead_time,
                "standard_price": pv.standard_price,
                "min_order_qty": pv.min_order_qty,
                "max_order_qty": pv.max_order_qty,
                "on_order_qty": pv.on_order_qty,
            })
        return Response({"results": data, "count": len(data)})
