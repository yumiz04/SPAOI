from rest_framework import viewsets
from rest_framework.exceptions import ValidationError

from apps.core.permissions import DeleteRole, ReadOnlyOrRole
from .filters import LotFilter
from .models import Lot
from .serializers import LotSerializer


class LotViewSet(viewsets.ModelViewSet):
    queryset = Lot.objects.exclude(status=Lot.Status.ELIMINADO).order_by("id")
    serializer_class = LotSerializer
    filterset_class = LotFilter
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    permission_classes = [ReadOnlyOrRole, DeleteRole]
    write_roles = ("inventory_manager",)
    delete_roles = ("inventory_manager",)

    def perform_create(self, serializer):
        from django.db import IntegrityError

        from apps.core.exceptions import AppError

        try:
            serializer.save()
        except IntegrityError:
            raise AppError(
                "DUPLICATE_LOT",
                "Ya existe un lote con ese número para el producto y ubicación",
                409,
            )

    def perform_destroy(self, instance):
        instance.status = Lot.Status.ELIMINADO
        instance.save(update_fields=["status", "updated_at"])