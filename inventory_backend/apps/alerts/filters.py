from django_filters import rest_framework as filters

from .models import Alert


class AlertFilter(filters.FilterSet):
    """El endpoint expone ?type=..., que mapea a la columna alert_type."""
    type = filters.ChoiceFilter(field_name="alert_type", choices=Alert.Type.choices)

    class Meta:
        model = Alert
        fields = ["alert_type", "severity", "status", "product_id"]