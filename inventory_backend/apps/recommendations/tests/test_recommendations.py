import datetime

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from apps.analytics.models import AnalysisRecord
from apps.core.dates import as_of_date
from apps.inventory.models import Location, ProductInventory
from apps.products.models import Product
from apps.purchasing.models import ProductVendor, Vendor
from apps.sales.models import SalesOrderDetail, SalesOrderHeader

AS_OF = as_of_date()
WINDOW = 90


@pytest.fixture
def analyst(db):
    user = User.objects.create_user("rec_analyst", password="x")
    user.groups.add(Group.objects.get_or_create(name="analyst")[0])
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def viewer(db):
    user = User.objects.create_user("rec_viewer", password="x")
    client = APIClient()
    client.force_authenticate(user)
    return client


def _ventas_diarias(product, order_base):
    """Una venta de 1 unidad por día dentro de la ventana: demanda diaria = 1."""
    inicio = AS_OF - datetime.timedelta(days=WINDOW)
    for offset in range(1, WINDOW + 1):
        dia = datetime.datetime.combine(
            inicio + datetime.timedelta(days=offset), datetime.time(10, 0),
            tzinfo=datetime.timezone.utc,
        )
        header = SalesOrderHeader.objects.create(id=order_base + offset, order_date=dia, status=5)
        SalesOrderDetail.objects.create(
            order=header, detail_id=1, product=product, order_qty=1, unit_price="10.0000"
        )


@pytest.fixture
def catalogo(db):
    Location.objects.create(id=5, name="Metal Storage")
    Location.objects.create(id=10, name="Frame Forming")

    reponer = Product.objects.create(
        id=680, name="HL Road Frame", product_number="FR-680", color="Black",
        safety_stock_level=5, reorder_point=5, standard_cost="10.00", list_price="20.00",
    )
    redistribuir = Product.objects.create(
        id=681, name="HL Road Frame XL", product_number="FR-681", color="Black",
        safety_stock_level=5, reorder_point=5, standard_cost="10.00", list_price="20.00",
    )

    # 681 tiene stock concentrado en la ubicación 10 y nada en la 5 -> hay traspaso.
    ProductInventory.objects.create(
        pk=(681, 10), product=redistribuir, location_id=10, shelf="A", bin=1,
        quantity=200, modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    ProductInventory.objects.create(
        pk=(681, 5), product=redistribuir, location_id=5, shelf="A", bin=1,
        quantity=0, modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )

    vendor = Vendor.objects.create(
        id=1, account_number="V-1", name="Proveedor Uno", credit_rating=5, active_flag=True
    )
    for producto in (reponer, redistribuir):
        ProductVendor.objects.create(
            product=producto, vendor=vendor, average_lead_time=14, standard_price="10.00",
            min_order_qty=1, max_order_qty=100, on_order_qty=0,
        )

    _ventas_diarias(reponer, 1000)
    _ventas_diarias(redistribuir, 2000)
    return {"reponer": reponer, "redistribuir": redistribuir}


@pytest.mark.django_db
def test_reposicion_propone_con_cifras_justificativas(analyst, catalogo):
    r = analyst.post("/api/recommendations/replenishment", {"product_id": 680}, format="json")

    assert r.status_code == 200
    assert r.data["is_proposal"] is True
    propuesta = r.data["results"][0]
    assert propuesta["product_id"] == 680
    assert propuesta["action"] == "PROPONER_ORDEN"
    # target = 1 * (14 + 7) + 5 = 26
    assert propuesta["suggested_quantity"] == 26
    assert propuesta["suggested_vendor_id"] == 1
    assert propuesta["justification"]["daily_demand"] == 1.0
    assert propuesta["justification"]["lead_time_days"] == 14
    assert propuesta["justification"]["stock"] == 0
    assert propuesta["expected_arrival"] == (AS_OF + datetime.timedelta(days=14)).isoformat()


@pytest.mark.django_db
def test_reposicion_no_toca_tablas_de_aw(analyst, catalogo):
    inventario_antes = ProductInventory.objects.count()
    ventas_antes = SalesOrderDetail.objects.count()

    analyst.post("/api/recommendations/replenishment", {"product_id": 680}, format="json")

    assert ProductInventory.objects.count() == inventario_antes
    assert SalesOrderDetail.objects.count() == ventas_antes
    assert AnalysisRecord.objects.filter(analysis_type="replenishment").count() == 1


@pytest.mark.django_db
def test_redistribucion_propone_traspaso_con_coberturas(analyst, catalogo):
    r = analyst.post("/api/recommendations/redistribution", {"product_id": 681}, format="json")

    assert r.status_code == 200
    propuesta = r.data["results"][0]
    assert propuesta["is_proposal"] is True
    transferencia = propuesta["transfers"][0]
    assert transferencia["from_location"] == 10
    assert transferencia["to_location"] == 5
    # d_i = 1/2 = 0.5; deficit receptor = 0.5 * 14 = 7
    assert transferencia["quantity"] == 7
    assert transferencia["reason"]["min_cover_days"] == 14
    assert transferencia["reason"]["max_cover_days"] == 180


@pytest.mark.django_db
def test_producto_inexistente_es_404(analyst, catalogo):
    r = analyst.post("/api/recommendations/replenishment", {"product_id": 999999}, format="json")

    assert r.status_code == 404
    assert r.data["code"] == "PRODUCT_NOT_FOUND"


@pytest.mark.django_db
def test_viewer_no_puede_proponer_403(viewer, catalogo):
    r = viewer.post("/api/recommendations/replenishment", {"product_id": 680}, format="json")

    assert r.status_code == 403


@pytest.mark.django_db
def test_anonimo_es_401(catalogo):
    assert APIClient().post(
        "/api/recommendations/replenishment", {"product_id": 680}, format="json"
    ).status_code == 401
