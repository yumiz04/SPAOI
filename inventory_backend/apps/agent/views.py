from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import AppError
from apps.core.permissions import user_in_groups
from . import registry


class ToolCatalogView(APIView):
    """Catálogo de herramientas en formato compatible con function calling."""

    throttle_scope = "agent"

    @extend_schema(
        summary="Catálogo de herramientas del agente",
        description=(
            "Devuelve las herramientas disponibles con su descripción, JSON Schema de "
            "entrada y si son de escritura (mutating). Compatible con function calling."
        ),
        responses={200: OpenApiResponse(description="Lista de herramientas")},
        tags=["agent"],
    )
    def get(self, request):
        return Response(registry.catalog())


class ToolExecuteView(APIView):
    """Ejecuta una herramienta. Siempre responde 200 con el envelope success/data/message.

    Las tools de escritura (crear_alerta, atender_alerta) exigen rol inventory_manager.
    """

    throttle_scope = "agent"

    @extend_schema(
        summary="Ejecutar una herramienta del agente",
        description=(
            "Ejecuta la herramienta indicada y deja traza en agent_tool_log. Nunca lanza "
            "una excepción al cliente: ante error devuelve HTTP 200 con "
            "``success=false`` y un ``code`` (VALIDATION_ERROR, TOOL_NOT_FOUND, etc.). "
            "Las tools de escritura requieren el rol inventory_manager."
        ),
        request=None,
        responses={200: OpenApiResponse(description="Envelope success/data/message")},
        tags=["agent"],
    )
    def post(self, request, name):
        spec = registry.TOOLS.get(name)
        if spec and spec.mutating and not user_in_groups(request.user, "inventory_manager"):
            raise AppError("PERMISSION_DENIED", "Se requiere rol inventory_manager", 403)
        result = registry.execute(
            name,
            request.data.get("parameters"),
            user=request.user,
            conversation_id=request.data.get("conversation_id"),
            user_request=request.data.get("user_request"),
        )
        return Response(result)
