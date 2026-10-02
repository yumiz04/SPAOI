from rest_framework import viewsets
from rest_framework.response import Response

from apps.core.permissions import ReadOnlyOrRole
from .filters import AlertFilter
from .models import Alert
from .serializers import AlertCreateSerializer, AlertSerializer, AlertStatusSerializer
from .services import AlertService


class AlertViewSet(viewsets.ModelViewSet):
    """RF-B15. Sin DELETE: las alertas se cierran, no se borran."""
    serializer_class = AlertSerializer
    filterset_class = AlertFilter
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_classes = [ReadOnlyOrRole]
    write_roles = ("inventory_manager",)

    def get_queryset(self):
        return AlertService.list(self.request.query_params)

    def get_serializer_class(self):
        if self.action == "create":
            return AlertCreateSerializer
        if self.action == "partial_update":
            return AlertStatusSerializer
        return AlertSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        alerta = serializer.save()
        return Response({"success": True, "data": AlertSerializer(alerta).data,
                         "message": "Alerta creada", "code": None}, status=201)

    def partial_update(self, request, *args, **kwargs):
        alerta = self.get_object()
        serializer = AlertStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        actualizada = AlertService.update_status(alerta.id, serializer.validated_data["status"])
        return Response({"success": True, "data": AlertSerializer(actualizada).data,
                         "message": "Alerta actualizada", "code": None})