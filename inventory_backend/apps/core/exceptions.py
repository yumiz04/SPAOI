import logging
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_handler

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Error de dominio controlado."""
    def __init__(self, code: str, message: str, http_status: int = 400):
        self.code, self.message, self.http_status = code, message, http_status
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, code="NOT_FOUND", message="Recurso no encontrado"):
        super().__init__(code, message, 404)


_DEFAULT_CODES = {400: "VALIDATION_ERROR", 401: "NOT_AUTHENTICATED", 403: "PERMISSION_DENIED",
                  404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 409: "CONFLICT", 429: "THROTTLED"}


def custom_exception_handler(exc, context):
    if isinstance(exc, AppError):
        return Response({"success": False, "data": None, "message": exc.message, "code": exc.code},
                        status=exc.http_status)
    response = drf_handler(exc, context)
    if response is None:                                    # error no controlado
        logger.exception("Unhandled error", exc_info=exc)
        return Response({"success": False, "data": None,
                         "message": "Error interno del servidor", "code": "INTERNAL_ERROR"}, status=500)
    detail = response.data
    message = detail.get("detail") if isinstance(detail, dict) and "detail" in detail else "Solicitud inválida"
    response.data = {"success": False,
                     "data": detail if response.status_code == 400 else None,
                     "message": str(message),
                     "code": _DEFAULT_CODES.get(response.status_code, "ERROR")}
    return response