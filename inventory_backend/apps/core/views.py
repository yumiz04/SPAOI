from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView


class PingView(APIView):
    @extend_schema(
        summary="Comprobación de salud",
        responses={200: OpenApiTypes.OBJECT},
        tags=["core"],
    )
    def get(self, request):
        return Response({"status": "ok", "user": request.user.username})
