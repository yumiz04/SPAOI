import django_filters as df

from .models import ProductInventory, TransactionHistory


class InventoryFilter(df.FilterSet):
    product = df.NumberFilter(field_name="product_id")
    product_id = df.NumberFilter(field_name="product_id")
    location = df.NumberFilter(field_name="location_id")
    location_id = df.NumberFilter(field_name="location_id")
    minimum_quantity = df.NumberFilter(field_name="quantity", lookup_expr="gte")
    maximum_quantity = df.NumberFilter(field_name="quantity", lookup_expr="lte")

    class Meta:
        model = ProductInventory
        fields = []


class MovementFilter(df.FilterSet):
    product = df.NumberFilter(field_name="product_id")
    date_from = df.DateFilter(field_name="transaction_date", lookup_expr="date__gte")
    date_to = df.DateFilter(field_name="transaction_date", lookup_expr="date__lte")
    type = df.CharFilter(field_name="transaction_type")

    class Meta:
        model = TransactionHistory
        fields = []
