from rest_framework.generics import ListAPIView

from apps.core.exceptions import AppError
from apps.sales.filters import SalesFilter
from apps.sales.models import SalesOrderDetail
from apps.sales.serializers import SalesRowSerializer


class SalesListView(ListAPIView):
    serializer_class = SalesRowSerializer
    filterset_class = SalesFilter
    ordering_fields = ["order__order_date", "product_id", "order_qty"]

    def get_queryset(self):
        qs = (
            SalesOrderDetail.objects
            .select_related("order", "product")
            .order_by("order__order_date", "product_id")
        )

        start = self.request.query_params.get("start_date")
        end = self.request.query_params.get("end_date")
        if start and end and start > end:
            raise AppError("INVALID_DATE_RANGE", "La fecha inicial es posterior a la final", 400)
        return qs
