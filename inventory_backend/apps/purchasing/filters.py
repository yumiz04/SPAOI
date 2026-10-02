import django_filters as df

from apps.purchasing.models import PurchaseOrderDetail


class PurchaseFilter(df.FilterSet):
    product = df.NumberFilter(field_name="product_id")
    product_id = df.NumberFilter(field_name="product_id")
    vendor = df.NumberFilter(field_name="order__vendor_id")
    status = df.NumberFilter(field_name="order__status")
    start_date = df.DateFilter(field_name="order__order_date", lookup_expr="date__gte")
    end_date = df.DateFilter(field_name="order__order_date", lookup_expr="date__lte")

    class Meta:
        model = PurchaseOrderDetail
        fields = []
