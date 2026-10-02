from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source="subcategory.category.name", default=None, read_only=True)
    subcategory_name = serializers.CharField(source="subcategory.name", default=None, read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "product_number", "color", "standard_cost", "list_price",
                  "safety_stock_level", "reorder_point", "category", "subcategory_name"]