from rest_framework import serializers

RISK_LEVELS = ("CRITICO", "ALTO", "MEDIO", "BAJO")
SEVERITIES = ("CRITICO", "ALTO", "MEDIO", "BAJO")


class StockoutQuerySerializer(serializers.Serializer):
    risk_min = serializers.ChoiceField(choices=RISK_LEVELS, default="MEDIO")
    product_id = serializers.IntegerField(required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500)


class DepletionQuerySerializer(serializers.Serializer):
    risk_min = serializers.ChoiceField(choices=RISK_LEVELS, default="MEDIO")
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500)


class TurnoverQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500)


class OverstockQuerySerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500)


class ExpirationQuerySerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False)
    severity = serializers.ChoiceField(choices=("CADUCADO", "ALTO", "MEDIO", "BAJO"), required=False)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=500)