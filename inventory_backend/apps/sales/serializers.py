from rest_framework import serializers


class SalesRowSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField(source="product.name")
    order_id = serializers.IntegerField()
    detail_id = serializers.IntegerField()
    order_qty = serializers.IntegerField()
    unit_price = serializers.DecimalField(max_digits=19, decimal_places=4)
    order_date = serializers.DateTimeField(source="order.order_date")
