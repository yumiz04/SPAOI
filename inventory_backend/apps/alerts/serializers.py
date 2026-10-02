from rest_framework import serializers

from .models import Alert


class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = [
            "id", "product_id", "location_id", "alert_type", "severity",
            "message", "details", "status", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AlertCreateSerializer(serializers.Serializer):
    """Alta manual (RF-B15)."""
    product_id = serializers.IntegerField()
    location_id = serializers.IntegerField(required=False, allow_null=True)
    alert_type = serializers.ChoiceField(choices=Alert.Type.choices)
    severity = serializers.ChoiceField(choices=Alert.Severity.choices)
    message = serializers.CharField()
    details = serializers.JSONField(required=False)

    def create(self, validated_data):
        from .services import AlertService

        return AlertService.create(**validated_data)


class AlertStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Alert.Status.ATENDIDA, Alert.Status.DESCARTADA])