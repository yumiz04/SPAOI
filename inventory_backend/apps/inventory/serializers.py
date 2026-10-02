from rest_framework import serializers
from .models import Location, ProductInventory, TransactionHistory


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name"]


class InventoryRowSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    location_name = serializers.CharField(source="location.name")

    class Meta:
        model = ProductInventory
        fields = [
            "product_id",
            "product_name",
            "location_id",
            "location_name",
            "quantity",
            "shelf",
            "bin",
        ]


class MovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", default=None)

    class Meta:
        model = TransactionHistory
        fields = [
            "id",
            "product_id",
            "product_name",
            "reference_order_id",
            "transaction_date",
            "transaction_type",
            "quantity",
            "actual_cost",
        ]
