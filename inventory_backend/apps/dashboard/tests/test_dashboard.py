import datetime

import pytest
from django.core.cache import cache
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from apps.alerts.models import Alert
from apps.inventory.models import Location, ProductInventory
from apps.products.models import Product

ESPERADAS = {
    "total_products",
    "total_inventory",
    "low_stock_products",
    "stockout_risks",
    "expiring_products",
    "overstock_products",
    "low_turnover_products",
    "pending_alerts",
}


@pytest.fixture(autouse=True)
def _limpiar_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def datos(db):
    Location.objects.create(id=5, name="Metal Storage")
    producto = Product.objects.create(
        id=680, name="HL Road Frame", product_number="FR-680", color="Black",
        safety_stock_level=100, reorder_point=50, standard_cost="10.00", list_price="20.00",
    )
    ProductInventory.objects.create(
        pk=(680, 5), product=producto, location_id=5, shelf="A", bin=1, quantity=10,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    Alert.objects.create(
        product_id=680, alert_type=Alert.Type.BAJO_STOCK, severity=Alert.Severity.MEDIA,
        message="bajo stock", dedup_key="BAJO_STOCK:680:0",
    )
    return producto


@pytest.mark.django_db
def test_summary_devuelve_las_ocho_claves(api, datos):
    r = api.get("/api/dashboard/summary")

    assert r.status_code == 200
    assert set(r.data.keys()) == ESPERADAS
    assert r.data["total_products"] == 1
    assert r.data["total_inventory"] == 10
    assert r.data["low_stock_products"] == 1
    assert r.data["stockout_risks"] == 0
    assert r.data["expiring_products"] == 0
    assert r.data["overstock_products"] == 0
    assert r.data["low_turnover_products"] == 1
    assert r.data["pending_alerts"] == 1


@pytest.mark.django_db
def test_segunda_llamada_sale_de_cache(api, datos):
    api.get("/api/dashboard/summary")

    with CaptureQueriesContext(connection) as capturadas:
        r = api.get("/api/dashboard/summary")

    assert r.status_code == 200
    assert len(capturadas.captured_queries) == 0


@pytest.mark.django_db
def test_las_cifras_coinciden_con_los_analyzers(api, datos):
    from apps.analytics.analyzers.stockout import StockoutAnalyzer

    r = api.get("/api/dashboard/summary")

    assert r.data["stockout_risks"] == len(StockoutAnalyzer.run(risk_min="ALTO"))


@pytest.mark.django_db
def test_anonimo_es_401(datos):
    assert APIClient().get("/api/dashboard/summary").status_code == 401
