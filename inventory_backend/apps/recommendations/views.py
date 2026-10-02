from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import ReadOnlyOrRole
from .serializers import RecommendationQuerySerializer
from .services import RecommendationService


class ReplenishmentView(APIView):
    """RF-B16. Propuesta de reposición; no crea órdenes de compra (RN-B04)."""

    permission_classes = [ReadOnlyOrRole]
    write_roles = ("analyst", "inventory_manager")

    @extend_schema(
        summary="Propuesta de reposición (no crea órdenes)",
        request=RecommendationQuerySerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["recommendations"],
    )
    def post(self, request):
        q = RecommendationQuerySerializer(data=request.data)
        q.is_valid(raise_exception=True)
        results = RecommendationService.replenishment(**q.validated_data)
        return Response({"is_proposal": True, "count": len(results), "results": results})


class RedistributionView(APIView):
    """RF-B17. Propuesta de traspasos entre ubicaciones; no persiste transferencias."""

    permission_classes = [ReadOnlyOrRole]
    write_roles = ("analyst", "inventory_manager")

    @extend_schema(
        summary="Propuesta de redistribución entre ubicaciones (no persiste transferencias)",
        request=RecommendationQuerySerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["recommendations"],
    )
    def post(self, request):
        q = RecommendationQuerySerializer(data=request.data)
        q.is_valid(raise_exception=True)
        results = RecommendationService.redistribution(**q.validated_data)
        return Response({"is_proposal": True, "count": len(results), "results": results})
