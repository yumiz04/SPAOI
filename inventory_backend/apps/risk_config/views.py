from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ReadOnlyOrRole
from .models import RiskConfig
from .serializers import RiskConfigSerializer
from .services import RiskConfigService


class RiskConfigView(APIView):
    """Parametros de riesgo efectivos (GET) y edicion de una capa (PATCH).

    GET  /api/risk-config?product_id=&category_id=  -> RiskParams ya resueltos
    PATCH /api/risk-config {"product_id": null, "category_id": null, ...} -> upsert de esa capa
    """

    permission_classes = [ReadOnlyOrRole]
    write_roles = ("inventory_manager",)

    @extend_schema(
        summary="Parámetros de riesgo efectivos",
        responses={200: OpenApiTypes.OBJECT},
        tags=["risk-config"],
    )
    def get(self, request):
        product_id = request.query_params.get("product_id")
        category_id = request.query_params.get("category_id")
        params = RiskConfigService.resolve(
            product_id=int(product_id) if product_id else None,
            category_id=int(category_id) if category_id else None,
        )
        return Response(params.to_dict())

    @extend_schema(
        summary="Editar (upsert) una capa de configuración de riesgo",
        request=RiskConfigSerializer,
        responses={200: RiskConfigSerializer, 201: RiskConfigSerializer},
        tags=["risk-config"],
    )
    def patch(self, request):
        data = request.data
        config, created = RiskConfig.objects.get_or_create(
            product_id=data.get("product_id"), category_id=data.get("category_id")
        )

        serializer = RiskConfigSerializer(config, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        RiskConfigService.invalidate()

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RiskConfigListView(APIView):
    """Todas las capas configuradas (global, categoria y producto)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Todas las capas de configuración de riesgo",
        responses={200: RiskConfigSerializer(many=True)},
        tags=["risk-config"],
    )
    def get(self, request):
        qs = RiskConfig.objects.order_by("product_id", "category_id")
        return Response(RiskConfigSerializer(qs, many=True).data)