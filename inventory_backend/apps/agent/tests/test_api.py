import datetime

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from apps.agent.models import ToolLog
from apps.inventory.models import Location, ProductInventory
from apps.products.models import Product


@pytest.fixture
def _cliente(db):
    def _make(*roles):
        user = User.objects.create_user(f"ag_{'-'.join(roles) or 'user'}", password="x")
        for role in roles:
            user.groups.add(Group.objects.get_or_create(name=role)[0])
        client = APIClient()
        client.force_authenticate(user)
        return client

    return _make


@pytest.fixture
def datos(db):
    location = Location.objects.create(id=5, name="Metal Storage")
    producto = Product.objects.create(
        id=680, name="HL Road Frame", product_number="FR-680", color="Black",
        safety_stock_level=500, reorder_point=375, standard_cost="10.00", list_price="20.00",
    )
    ProductInventory.objects.create(
        pk=(680, 5), product=producto, location=location, shelf="A", bin=1, quantity=120,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    return producto


def test_catalogo_lista_las_herramientas(_cliente, datos):
    r = _cliente("viewer").get("/api/agent/tools")

    assert r.status_code == 200
    nombres = {t["name"] for t in r.data}
    assert "obtener_existencias" in nombres
    assert "analizar_desabasto" in nombres
    assert "crear_alerta" in nombres
    assert all("input_schema" in t for t in r.data)


def test_ejecutar_herramienta_registra_traza(_cliente, datos):
    r = _cliente("viewer").post(
        "/api/agent/tools/analizar_desabasto/execute",
        {"parameters": {"riesgo_minimo": "BAJO"}, "user_request": "¿riesgo de agotarse?"},
        format="json",
    )

    assert r.status_code == 200
    assert r.data["success"] is True
    assert ToolLog.objects.count() == 1
    assert ToolLog.objects.latest("id").user_request == "¿riesgo de agotarse?"


def test_parametro_invalido_devuelve_success_false(_cliente, datos):
    r = _cliente("viewer").post(
        "/api/agent/tools/analizar_desabasto/execute",
        {"parameters": {"riesgo_minimo": "MALO"}},
        format="json",
    )

    assert r.status_code == 200
    assert r.data["success"] is False
    assert r.data["code"] == "VALIDATION_ERROR"


def test_herramienta_inexistente(_cliente, datos):
    r = _cliente("viewer").post(
        "/api/agent/tools/no_existe/execute", {"parameters": {}}, format="json"
    )

    assert r.status_code == 200
    assert r.data["success"] is False
    assert r.data["code"] == "TOOL_NOT_FOUND"


def test_crear_alerta_requiere_inventory_manager(_cliente, datos):
    payload = {
        "parameters": {
            "product_id": 680, "tipo": "BAJO_STOCK", "severidad": "MEDIA", "mensaje": "poco stock"
        }
    }
    r = _cliente("viewer").post(
        "/api/agent/tools/crear_alerta/execute", payload, format="json"
    )

    assert r.status_code == 403
    assert ToolLog.objects.count() == 0


def test_inventory_manager_puede_crear_alerta(_cliente, datos):
    payload = {
        "parameters": {
            "product_id": 680, "tipo": "BAJO_STOCK", "severidad": "MEDIA", "mensaje": "poco stock"
        }
    }
    r = _cliente("inventory_manager").post(
        "/api/agent/tools/crear_alerta/execute", payload, format="json"
    )

    assert r.status_code == 200
    assert r.data["success"] is True
    assert r.data["data"]["alert_type"] == "BAJO_STOCK"


def test_anonimo_es_401(datos):
    assert APIClient().get("/api/agent/tools").status_code == 401


def test_las_vistas_del_agente_estan_limitedas():
    from apps.agent.views import ToolCatalogView, ToolExecuteView

    assert ToolCatalogView.throttle_scope == "agent"
    assert ToolExecuteView.throttle_scope == "agent"


def test_el_esquema_openapi_se_genera(_cliente, datos):
    r = _cliente("viewer").get("/api/schema/")

    assert r.status_code == 200
