from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .analyzers.depletion import DepletionAnalyzer
from .analyzers.expiration import ExpirationAnalyzer
from .analyzers.inventory import InventoryAnalyzer
from .analyzers.overstock import OverstockAnalyzer
from .analyzers.stockout import StockoutAnalyzer
from .analyzers.turnover import TurnoverAnalyzer
from .models import AnalysisRecord
from .serializers import (
    DepletionQuerySerializer,
    ExpirationQuerySerializer,
    OverstockQuerySerializer,
    StockoutQuerySerializer,
    TurnoverQuerySerializer,
)


def _persist(analysis_type, parameters, result, version, product_id=None):
    """RN-B05: cada ejecucion relevante queda conservada para trazabilidad."""
    AnalysisRecord.objects.create(
        analysis_type=analysis_type,
        product_id=product_id,
        parameters=parameters,
        result=result,
        algorithm_version=version,
    )


class StockoutView(APIView):
    @extend_schema(
        summary="Riesgo de desabasto",
        parameters=[StockoutQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request):
        q = StockoutQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        params = q.validated_data
        result = StockoutAnalyzer.run(**params)
        _persist("stockout", params, result, StockoutAnalyzer.VERSION)
        return Response(result)


class DepletionView(APIView):
    @extend_schema(
        summary="Fecha estimada de agotamiento",
        parameters=[DepletionQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request):
        q = DepletionQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        params = q.validated_data
        result = DepletionAnalyzer.run(**params)
        _persist("depletion", params, result, DepletionAnalyzer.VERSION)
        return Response(result)


class DepletionByProductView(APIView):
    @extend_schema(
        summary="Agotamiento estimado de un producto",
        operation_id="analytics_depletion_by_product",
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request, product_id: int):
        result = DepletionAnalyzer.run_for_product(product_id)
        _persist("depletion_product", {"product_id": product_id}, result, DepletionAnalyzer.VERSION, product_id)
        return Response(result)


class TurnoverView(APIView):
    @extend_schema(
        summary="Rotación de inventario",
        parameters=[TurnoverQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request):
        q = TurnoverQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        params = q.validated_data
        result = TurnoverAnalyzer.run(**params)
        _persist("turnover", params, result, TurnoverAnalyzer.VERSION)
        return Response(result)


class OverstockView(APIView):
    @extend_schema(
        summary="Sobreinventario",
        parameters=[OverstockQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request):
        q = OverstockQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        params = q.validated_data
        result = OverstockAnalyzer.run(**params)
        _persist("overstock", params, result, OverstockAnalyzer.VERSION)
        return Response(result)


class ExpirationView(APIView):
    @extend_schema(
        summary="Caducidades próximas",
        parameters=[ExpirationQuerySerializer],
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request):
        q = ExpirationQuerySerializer(data=request.query_params)
        q.is_valid(raise_exception=True)
        params = q.validated_data
        result = ExpirationAnalyzer.run(**params)
        _persist("expiration", params, result, ExpirationAnalyzer.VERSION)
        return Response(result)


class InventoryTotalsView(APIView):
    @extend_schema(
        summary="Totales de inventario y valor por categoría",
        responses={200: OpenApiTypes.OBJECT},
        tags=["analytics"],
    )
    def get(self, request):
        result = InventoryAnalyzer.run()
        _persist("inventory", {}, result, InventoryAnalyzer.VERSION)
        return Response(result)
