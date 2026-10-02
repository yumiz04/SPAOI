from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.inventory.models import Location
from apps.products.models import Product
from .models import Lot


class LotSerializer(serializers.ModelSerializer):
    days_remaining = serializers.SerializerMethodField()

    class Meta:
        model = Lot
        fields = [
            "id",
            "product_id",
            "location_id",
            "lot_number",
            "quantity",
            "entry_date",
            "expiration_date",
            "status",
            "days_remaining",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # La unicidad la resuelve perform_create -> IntegrityError -> 409 DUPLICATE_LOT,
        # no el 400 genérico de DRF.
        self.validators = [
            v
            for v in self.validators
            if not (
                isinstance(v, UniqueTogetherValidator)
                and set(v.fields) == {"product_id", "location_id", "lot_number"}
            )
        ]

    def get_days_remaining(self, obj) -> int | None:
        from apps.core.dates import as_of_date

        return (obj.expiration_date - as_of_date()).days if obj.expiration_date else None

    def validate_product_id(self, value):
        if not Product.objects.filter(pk=value).exists():
            raise serializers.ValidationError("El producto no existe en AdventureWorks")
        return value

    def validate_location_id(self, value):
        if not Location.objects.filter(pk=value).exists():
            raise serializers.ValidationError("La ubicación no existe")
        return value

    def validate(self, attrs):
        entry = attrs.get("entry_date", getattr(self.instance, "entry_date", None))
        exp = attrs.get("expiration_date", getattr(self.instance, "expiration_date", None))
        if entry and exp and exp < entry:
            raise serializers.ValidationError(
                "La caducidad no puede ser anterior a la entrada"
            )
        return attrs