import datetime

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.core.dates import as_of_date
from apps.inventory.models import Location
from apps.lots.models import Lot
from apps.products.models import Product

PRODUCT_ID = 316
LOCATION_ID = 5


@pytest.fixture
def catalogo(db):
    """El servicio valida contra AdventureWorks; en la BD de pruebas sembramos el mínimo."""
    Product.objects.create(
        id=PRODUCT_ID,
        name="Blade",
        product_number="BL-123",
        color="Black",
        safety_stock_level=100,
        reorder_point=50,
        standard_cost="0.00",
        list_price="0.00",
    )
    return Location.objects.create(id=LOCATION_ID, name="Metal Storage")


@pytest.fixture
def manager(db):
    from django.contrib.auth.models import Group, User

    user = User.objects.create_user("lot_mgr", password="x")
    user.groups.add(Group.objects.get_or_create(name="inventory_manager")[0])
    client = APIClient()
    client.force_authenticate(user)
    return client


def _payload(**overrides):
    data = {
        "product_id": PRODUCT_ID,
        "location_id": LOCATION_ID,
        "lot_number": "L-T-1",
        "quantity": 10,
        "entry_date": "2014-01-01",
        "expiration_date": "2015-01-01",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_crear_lote_devuelve_201(manager, catalogo):
    r = manager.post("/api/lots", _payload(), format="json")

    assert r.status_code == 201
    assert r.data["status"] == Lot.Status.ACTIVO
    assert Lot.objects.filter(pk=r.data["id"]).exists()


@pytest.mark.django_db
def test_lote_duplicado_devuelve_409(manager, catalogo):
    manager.post("/api/lots", _payload(), format="json")

    r = manager.post("/api/lots", _payload(), format="json")

    assert r.status_code == 409
    assert r.data["code"] == "DUPLICATE_LOT"


@pytest.mark.django_db
def test_producto_inexistente_es_400(manager, catalogo):
    r = manager.post("/api/lots", _payload(product_id=999999), format="json")

    assert r.status_code == 400


@pytest.mark.django_db
def test_caducidad_anterior_a_entrada_es_400(manager, catalogo):
    r = manager.post(
        "/api/lots",
        _payload(entry_date="2014-06-01", expiration_date="2014-01-01"),
        format="json",
    )

    assert r.status_code == 400


@pytest.mark.django_db
def test_delete_es_baja_logica(manager, catalogo):
    creado = manager.post("/api/lots", _payload(), format="json").data["id"]

    r = manager.delete(f"/api/lots/{creado}")

    assert r.status_code == 204
    assert Lot.objects.get(pk=creado).status == Lot.Status.ELIMINADO
    assert creado not in [lote["id"] for lote in manager.get("/api/lots").data["results"]]


@pytest.mark.django_db
def test_viewer_no_puede_crear(catalogo):
    from django.contrib.auth.models import Group, User

    user = User.objects.create_user("lot_viewer", password="x")
    user.groups.add(Group.objects.get_or_create(name="viewer")[0])
    client = APIClient()
    client.force_authenticate(user)

    r = client.post("/api/lots", _payload(), format="json")

    assert r.status_code == 403
    assert client.get("/api/lots").status_code == 200


@pytest.mark.django_db
def test_expiring_solo_devuelve_activos_no_vencidos():
    from apps.lots.services import LotService

    Lot.objects.create(
        product_id=PRODUCT_ID,
        location_id=LOCATION_ID,
        lot_number="VENCIDO",
        quantity=1,
        entry_date="2013-01-01",
        expiration_date=as_of_date() - datetime.timedelta(days=5),
        status=Lot.Status.CADUCADO,
    )
    proximo = Lot.objects.create(
        product_id=PRODUCT_ID,
        location_id=LOCATION_ID,
        lot_number="PROXIMO",
        quantity=1,
        entry_date="2014-01-01",
        expiration_date=as_of_date() + datetime.timedelta(days=10),
    )
    lejano = Lot.objects.create(
        product_id=PRODUCT_ID,
        location_id=LOCATION_ID,
        lot_number="LEJANO",
        quantity=1,
        entry_date="2014-01-01",
        expiration_date=as_of_date() + datetime.timedelta(days=200),
    )

    ids = [lote.pk for lote in LotService.expiring(30)]

    assert proximo.pk in ids
    assert lejano.pk not in ids


@pytest.mark.django_db
def test_reconcile_reporta_diferencia(catalogo):
    from apps.inventory.models import ProductInventory
    from apps.lots.services import LotService

    ProductInventory.objects.create(
        product_id=PRODUCT_ID,
        location=catalogo,
        shelf="Z",
        bin=1,
        quantity=100,
        modified_date=timezone.now(),
    )
    Lot.objects.create(
        product_id=PRODUCT_ID,
        location_id=LOCATION_ID,
        lot_number="REC",
        quantity=70,
        entry_date="2014-01-01",
    )

    resultado = LotService.reconcile(PRODUCT_ID)

    assert resultado["lots_quantity"] == 70
    assert resultado["inventory_quantity"] == 100
    assert resultado["difference"] == 30