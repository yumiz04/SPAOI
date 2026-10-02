import django_filters as df
from apps.sales.models import SalesOrderDetail


class SalesFilter(df.FilterSet):
    product = df.NumberFilter(field_name="product_id")
    product_id = df.NumberFilter(field_name="product_id")
    start_date = df.DateFilter(field_name="order__order_date", lookup_expr="date__gte")
    end_date = df.DateFilter(field_name="order__order_date", lookup_expr="date__lte")

    class Meta:
        model = SalesOrderDetail
        fields = []
