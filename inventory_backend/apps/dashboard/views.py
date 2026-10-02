from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import DashboardService


class SummaryView(APIView):
    """RF-B18. Las 8 cifras del tablero, servidas desde caché."""

    @extend_schema(
        summary="Resumen del tablero (cacheado)",
        responses={200: OpenApiTypes.OBJECT},
        tags=["dashboard"],
    )
    def get(self, request):
        return Response(DashboardService.summary())
