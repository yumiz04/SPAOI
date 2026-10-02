from rest_framework import serializers

from .models import RiskConfig


class RiskConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskConfig
        fields = [
            "id",
            "product_id",
            "category_id",
            "min_stock",
            "expiry_warning_days",
            "overstock_days_of_cover",
            "analysis_period_days",
            "low_turnover_threshold",
            "high_turnover_threshold",
            "service_level_z",
            "review_period_days",
            "default_lead_time_days",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]

    def validate(self, attrs):
        low = attrs.get("low_turnover_threshold", getattr(self.instance, "low_turnover_threshold", None))
        high = attrs.get("high_turnover_threshold", getattr(self.instance, "high_turnover_threshold", None))
        if low is not None and high is not None and low >= high:
            raise serializers.ValidationError(
                "low_turnover_threshold debe ser menor que high_turnover_threshold"
            )
        return attrs