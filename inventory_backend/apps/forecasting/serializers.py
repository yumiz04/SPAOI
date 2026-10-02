from rest_framework import serializers

from .models import Forecast


class ForecastRequestSerializer(serializers.Serializer):
    """Entrada de POST /api/forecast."""
    product_id = serializers.IntegerField()
    historical_days = serializers.IntegerField(min_value=1, max_value=730, default=365)
    forecast_days = serializers.IntegerField(min_value=1, max_value=365, default=30)
    alpha = serializers.FloatField(min_value=0.01, max_value=0.99, required=False, default=0.3)


class ForecastSerializer(serializers.ModelSerializer):
    class Meta:
        model = Forecast
        fields = [
            "id", "product_id", "forecast_date", "forecast_quantity",
            "model_name", "model_version", "confidence", "created_at",
        ]