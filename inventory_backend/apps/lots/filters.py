import datetime

import django_filters as df

from .models import Lot


class LotFilter(df.FilterSet):
    product = df.NumberFilter(field_name="product_id")
    location = df.NumberFilter(field_name="location_id")
    status = df.ChoiceFilter(field_name="status", choices=Lot.Status.choices)
    expiring_within = df.NumberFilter(method="filter_expiring_within")
    order = df.OrderingFilter(
        fields=("expiration_date", "entry_date", "quantity", "product_id")
    )

    class Meta:
        model = Lot
        fields = []

    def filter_expiring_within(self, queryset, name, value):
        from apps.core.dates import as_of_date

        limit = as_of_date() + datetime.timedelta(days=int(value))
        return queryset.filter(
            status=Lot.Status.ACTIVO,
            expiration_date__isnull=False,
            expiration_date__lte=limit,
        )