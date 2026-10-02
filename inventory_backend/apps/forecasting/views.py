from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import ForecastRequestSerializer
from .services import ForecastService


class ForecastView(APIView):
    @extend_schema(
        summary="Pronóstico de demanda (SES)",
        request=ForecastRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
        tags=["forecasting"],
    )
    def post(self, request):
        q = ForecastRequestSerializer(data=request.data)
        q.is_valid(raise_exception=True)
        resultado = ForecastService.forecast(**q.validated_data)
        ForecastService.persist_analysis(resultado)
        return Response(resultado)