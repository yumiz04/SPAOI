import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from apps.alerts.models import Alert


@pytest.fixture
def manager(db):
    user = User.objects.create_user("alert_mgr", password="x")
    user.groups.add(Group.objects.get_or_create(name="inventory_manager")[0])
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def viewer(db):
    user = User.objects.create_user("alert_viewer", password="x")
    user.groups.add(Group.objects.get_or_create(name="viewer")[0])
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def alerta(db):
    return Alert.objects.create(
        product_id=316, location_id=5, alert_type=Alert.Type.DESABASTO,
        severity=Alert.Severity.CRITICA, message="Desabasto critico",
        details={"stock": 0}, dedup_key="DESABASTO:316:5",
    )


@pytest.mark.django_db
def test_listar_alertas(manager, alerta):
    r = manager.get("/api/alerts/")

    assert r.status_code == 200
    assert r.data["count"] == 1
    assert r.data["results"][0]["alert_type"] == "DESABASTO"
    # El sobre uniforme se aplica al renderizar la respuesta.
    cuerpo = r.json()
    assert cuerpo["success"] is True
    assert cuerpo["data"]["count"] == 1


@pytest.mark.django_db
def test_filtrar_por_tipo_severidad_estado_y_producto(manager, alerta):
    assert manager.get("/api/alerts/?type=DESABASTO").data["count"] == 1
    assert manager.get("/api/alerts/?type=SOBREINVENTARIO").data["count"] == 0
    assert manager.get("/api/alerts/?severity=CRITICA").data["count"] == 1
    assert manager.get("/api/alerts/?status=PENDIENTE").data["count"] == 1
    assert manager.get("/api/alerts/?product_id=316").data["count"] == 1
    assert manager.get("/api/alerts/?product_id=999").data["count"] == 0


@pytest.mark.django_db
def test_filtro_invalido_es_400(manager, alerta):
    r = manager.get("/api/alerts/?status=INVENTADO")

    assert r.status_code == 400
    assert r.data["code"] == "VALIDATION_ERROR"


@pytest.mark.django_db
def test_detalle_de_alerta(manager, alerta):
    r = manager.get(f"/api/alerts/{alerta.id}/")

    assert r.status_code == 200
    assert r.data["alert_type"] == "DESABASTO"
    assert r.data["details"] == {"stock": 0}


@pytest.mark.django_db
def test_crear_alerta_manual(manager, alerta):
    r = manager.post("/api/alerts/", {
        "product_id": 707, "location_id": 6, "alert_type": "SOBREINVENTARIO",
        "severity": "BAJA", "message": "Exceso manual", "details": {"excess_units": 12},
    }, format="json")

    assert r.status_code == 201
    assert r.data["data"]["alert_type"] == "SOBREINVENTARIO"


@pytest.mark.django_db
def test_crear_alerta_duplicada_es_409(manager, alerta):
    r = manager.post("/api/alerts/", {
        "product_id": 316, "location_id": 5, "alert_type": "DESABASTO",
        "severity": "CRITICA", "message": "Otra vez",
    }, format="json")

    assert r.status_code == 409
    assert r.data["code"] == "DUPLICATE_ALERT"


@pytest.mark.django_db
def test_patch_cierra_la_alerta(manager, alerta):
    r = manager.patch(f"/api/alerts/{alerta.id}/", {"status": "ATENDIDA"}, format="json")

    assert r.status_code == 200
    assert r.data["data"]["status"] == "ATENDIDA"


@pytest.mark.django_db
def test_patch_de_alerta_ya_atendida_es_409(manager, alerta):
    manager.patch(f"/api/alerts/{alerta.id}/", {"status": "ATENDIDA"}, format="json")

    r = manager.patch(f"/api/alerts/{alerta.id}/", {"status": "DESCARTADA"}, format="json")

    assert r.status_code == 409
    assert r.data["code"] == "ALERT_ALREADY_CLOSED"


@pytest.mark.django_db
def test_patch_a_estado_no_permitido_es_400(manager, alerta):
    r = manager.patch(f"/api/alerts/{alerta.id}/", {"status": "PENDIENTE"}, format="json")

    assert r.status_code == 400


@pytest.mark.django_db
def test_viewer_no_puede_hacer_patch(viewer, alerta):
    r = viewer.patch(f"/api/alerts/{alerta.id}/", {"status": "ATENDIDA"}, format="json")

    assert r.status_code == 403


@pytest.mark.django_db
def test_viewer_no_puede_crear(viewer, alerta):
    r = viewer.post("/api/alerts/", {
        "product_id": 707, "alert_type": "SOBREINVENTARIO", "severity": "BAJA",
        "message": "no permitido",
    }, format="json")

    assert r.status_code == 403


@pytest.mark.django_db
def test_viewer_si_puede_leer(viewer, alerta):
    assert viewer.get("/api/alerts/").status_code == 200


@pytest.mark.django_db
def test_no_hay_delete(viewer, alerta):
    """RF-B15: las alertas se cierran, no se eliminan."""
    assert manager_delete(viewer, alerta.id) in (403, 405)


def manager_delete(client, alert_id):
    return client.delete(f"/api/alerts/{alert_id}/").status_code


@pytest.mark.django_db
def test_anónimo_es_401(alerta):
    assert APIClient().get("/api/alerts/").status_code == 401