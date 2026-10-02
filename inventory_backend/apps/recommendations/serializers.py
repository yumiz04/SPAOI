from rest_framework import serializers


class RecommendationQuerySerializer(serializers.Serializer):
    """Entrada de las propuestas: se puede acotar a un producto o a una categoría."""

    product_id = serializers.IntegerField(required=False)
    category = serializers.IntegerField(required=False)
