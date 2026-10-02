import pytest
from rest_framework.test import APIClient

from apps.risk_config.models import RiskConfig


@pytest.fixture(autouse=True)
def clear_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


def _client(username, role):
    from django.contrib.auth.models import Group, User

    user = User.objects.create_user(username, password="x")
    user.groups.add(Group.objects.get_or_create(name=role)[0])
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def manager(db):
    return _client("rc_api_mgr", "inventory_manager")


@pytest.fixture
def viewer(db):
    return _client("rc_api_viewer", "viewer")


@pytest.mark.django_db
def test_get_devuelve_defaults_sin_configuracion(manager):
    r = manager.get("/api/risk-config")

    assert r.status_code == 200
    assert r.data["expiry_warning_days"] == 30
    assert r.data["service_level_z"] == 1.65


@pytest.mark.django_db
def test_patch_crea_capa_y_resuelve_precedencia(manager):
    manager.patch("/api/risk-config", {"min_stock": 5, "expiry_warning_days": 45}, format="json")
    manager.patch("/api/risk-config", {"category_id": 7, "min_stock": 9}, format="json")

    r = manager.get("/api/risk-config", {"category_id": 7})

    assert r.data["min_stock"] == 9
    assert r.data["expiry_warning_days"] == 45


@pytest.mark.django_db
def test_patch_es_idempotente_sobre_la_misma_capa(manager):
    primero = manager.patch("/api/risk-config", {"min_stock": 5}, format="json")
    segundo = manager.patch("/api/risk-config", {"min_stock": 5}, format="json")

    assert primero.status_code == 201
    assert segundo.status_code == 200
    assert primero.data["id"] == segundo.data["id"]
    assert RiskConfig.objects.count() == 1


@pytest.mark.django_db
def test_patch_rechaza_umbrales_invertidos(manager):
    r = manager.patch(
        "/api/risk-config",
        {"low_turnover_threshold": 9, "high_turnover_threshold": 2},
        format="json",
    )

    assert r.status_code == 400


@pytest.mark.django_db
def test_patch_invalida_cache(manager):
    manager.patch("/api/risk-config", {"min_stock": 5}, format="json")
    assert manager.get("/api/risk-config").data["min_stock"] == 5

    manager.patch("/api/risk-config", {"min_stock": 42}, format="json")

    assert manager.get("/api/risk-config").data["min_stock"] == 42


@pytest.mark.django_db
def test_viewer_no_puede_editar(viewer):
    assert viewer.get("/api/risk-config").status_code == 200

    r = viewer.patch("/api/risk-config", {"min_stock": 5}, format="json")

    assert r.status_code == 403


@pytest.mark.django_db
def test_layers_devuelve_todas_las_capas(manager):
    manager.patch("/api/risk-config", {"min_stock": 5}, format="json")
    manager.patch("/api/risk-config", {"category_id": 7, "min_stock": 9}, format="json")
    manager.patch("/api/risk-config", {"product_id": 316, "min_stock": 20}, format="json")

    r = manager.get("/api/risk-config/layers")

    assert len(r.data) == 3