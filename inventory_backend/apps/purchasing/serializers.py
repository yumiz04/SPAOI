from rest_framework import serializers


class PurchaseRowSerializer(serializers.Serializer):
    product_id = serializers.IntegerField()
    product_name = serializers.CharField(source="product.name")
    order_id = serializers.IntegerField()
    detail_id = serializers.IntegerField()
    vendor_id = serializers.IntegerField(source="order.vendor_id")
    vendor_name = serializers.CharField(source="order.vendor.name", default=None)
    status = serializers.IntegerField(source="order.status")
    order_date = serializers.DateTimeField(source="order.order_date")
    due_date = serializers.DateTimeField()
    order_qty = serializers.IntegerField()
    received_qty = serializers.DecimalField(max_digits=8, decimal_places=2)
    rejected_qty = serializers.DecimalField(max_digits=8, decimal_places=2)
    unit_price = serializers.DecimalField(max_digits=19, decimal_places=4)
