import json
from rest_framework.exceptions import NotFound
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

from apps.core.exceptions import AppError, custom_exception_handler


def test_app_error_devuelve_envelope_y_status():
    response = custom_exception_handler(AppError("X", "msg", 409), context={})

    assert response.status_code == 409
    assert response.data["code"] == "X"
    assert response.data == {"success": False, "data": None, "message": "msg", "code": "X"}


def test_error_de_drf_se_convierte_a_envelope():
    response = custom_exception_handler(NotFound("no existe"), context={})

    assert response.status_code == 404
    assert response.data["success"] is False
    assert response.data["code"] == "NOT_FOUND"


def test_error_no_controlado_devuelve_500_sin_detalles():
    response = custom_exception_handler(RuntimeError("secreto interno"), context={})

    assert response.status_code == 500
    assert response.data["code"] == "INTERNAL_ERROR"
    assert "secreto" not in response.data["message"]      # no exponer información sensible


class _VistaQueFalla(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        raise AppError("X", "msg", 409)


def test_vista_completa_pasa_por_handler_y_renderer():
    request = APIRequestFactory().get("/boom")
    response = _VistaQueFalla.as_view()(request)
    response.render()

    assert response.status_code == 409
    assert json.loads(response.content) == {
        "success": False, "data": None, "message": "msg", "code": "X",
    }

def test_handler_registrado_en_settings():
    from rest_framework.settings import api_settings
    assert api_settings.EXCEPTION_HANDLER is custom_exception_handler