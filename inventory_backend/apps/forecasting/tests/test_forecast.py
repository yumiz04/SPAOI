import datetime

import pytest
from django.contrib.auth.models import Group, User
from rest_framework.test import APIClient

from apps.analytics.models import AnalysisRecord
from apps.core.dates import as_of_date
from apps.forecasting.models import Forecast
from apps.products.models import Product
from apps.sales.models import SalesOrderDetail, SalesOrderHeader

PRODUCT_ID = 707


@pytest.fixture
def manager(db):
    user = User.objects.create_user("fc_mgr", password="x")
    user.groups.add(Group.objects.get_or_create(name="inventory_manager")[0])
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def producto(db):
    return Product.objects.create(
        id=PRODUCT_ID, name="Mountain-100 Silver, 38", product_number="MO-707",
        color="Silver", safety_stock_level=10, reorder_point=5,
        standard_cost="10.00", list_price="20.00",
    )


@pytest.fixture
def ventas(producto):
    """Una venta cada 3 días dentro de la ventana, para tener días con y sin venta."""
    inicio = as_of_date() - datetime.timedelta(days=90)
    # offset >= 1: la serie cubre (as_of - 90, as_of], no incluye as_of - 90.
    for i, offset in enumerate(range(1, 90, 3), start=1):
        dia = datetime.datetime.combine(
            inicio + datetime.timedelta(days=offset), datetime.time(10, 0), tzinfo=datetime.timezone.utc
        )
        header = SalesOrderHeader.objects.create(id=i, order_date=dia, status=5)
        SalesOrderDetail.objects.create(
            order=header, detail_id=i, product=producto, order_qty=2, unit_price="10.0000"
        )
    return producto


@pytest.mark.django_db
def test_post_forecast_devuelve_los_dias_pedidos(manager, ventas):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 30,
    }, format="json")

    assert r.status_code == 200
    assert len(r.data["forecast"]) == 30
    assert r.data["model_name"] == "ses"
    assert r.data["product_id"] == PRODUCT_ID


@pytest.mark.django_db
def test_pronostico_plano_con_banda_simetrica(manager, ventas):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 5,
    }, format="json")

    fila = r.data["forecast"][0]
    assert fila["quantity"] == pytest.approx(r.data["level"], abs=0.01)
    assert fila["lower"] <= fila["quantity"] <= fila["upper"]
    # La banda es nivel ± 1.96 sigma y el tope inferior no puede ser negativo.
    assert fila["lower"] == pytest.approx(max(0.0, r.data["level"] - 1.96 * r.data["sigma"]), abs=0.01)
    assert fila["upper"] == pytest.approx(r.data["level"] + 1.96 * r.data["sigma"], abs=0.01)


@pytest.mark.django_db
def test_las_fechas_comienzan_al_dia_siguiente_de_as_of(manager, ventas):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 3,
    }, format="json")

    fechas = [f["forecast_date"] for f in r.data["forecast"]]
    assert fechas[0] == (as_of_date() + datetime.timedelta(days=1)).isoformat()
    assert fechas == sorted(fechas)


@pytest.mark.django_db
def test_persiste_un_registro_por_dia_y_la_corrida(manager, ventas):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 30,
    }, format="json")

    assert Forecast.objects.filter(product_id=PRODUCT_ID).count() == 30
    assert r.data["model_version"] == "1.0.0"
    assert AnalysisRecord.objects.filter(
        analysis_type="forecast", product_id=PRODUCT_ID
    ).count() == 1


@pytest.mark.django_db
def test_repetir_el_pronostico_no_duplica_filas(manager, ventas):
    cuerpo = {"product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 10}
    manager.post("/api/forecast", cuerpo, format="json")
    manager.post("/api/forecast", cuerpo, format="json")

    assert Forecast.objects.filter(product_id=PRODUCT_ID).count() == 10


@pytest.mark.django_db
def test_historical_days_cero_es_400(manager, ventas):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 0, "forecast_days": 30,
    }, format="json")

    assert r.status_code == 400
    assert "historical_days" in r.data["data"]


@pytest.mark.django_db
def test_rangos_fuera_de_limite_son_400(manager, ventas):
    assert manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 731, "forecast_days": 30,
    }, format="json").status_code == 400
    assert manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 366,
    }, format="json").status_code == 400


@pytest.mark.django_db
def test_producto_inexistente_es_404(manager, producto):
    r = manager.post("/api/forecast", {
        "product_id": 999999, "historical_days": 90, "forecast_days": 5,
    }, format="json")

    assert r.status_code == 404
    assert r.data["code"] == "PRODUCT_NOT_FOUND"


@pytest.mark.django_db
def test_historial_insuficiente_avisa(manager, producto):
    """Un solo día con ventas no alcanza los 14 días mínimos."""
    dia = datetime.datetime.combine(
        as_of_date(), datetime.time(10, 0), tzinfo=datetime.timezone.utc
    )
    header = SalesOrderHeader.objects.create(id=1, order_date=dia, status=5)
    SalesOrderDetail.objects.create(
        order=header, detail_id=1, product=producto, order_qty=4, unit_price="10.0000"
    )

    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 5,
    }, format="json")

    assert r.status_code == 200
    assert r.data["warning"] == "Historial insuficiente"
    assert r.data["inputs"]["days_with_data"] == 1


@pytest.mark.django_db
def test_serie_rellena_con_ceros(manager, ventas):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 5,
    }, format="json")

    # 30 ventas de 2 unidades en 90 días: los 60 días restantes cuentan como 0.
    assert r.data["inputs"]["total_units"] == 60
    assert r.data["inputs"]["days_with_data"] == 30
    assert "warning" not in r.data


@pytest.mark.django_db
def test_sin_ventas_devuelve_pronostico_en_cero(manager, producto):
    r = manager.post("/api/forecast", {
        "product_id": PRODUCT_ID, "historical_days": 90, "forecast_days": 5,
    }, format="json")

    assert r.status_code == 200
    assert r.data["level"] == 0.0
    assert r.data["confidence"] == 0.0
    assert all(f["quantity"] == 0.0 for f in r.data["forecast"])


@pytest.mark.django_db
def test_anónimo_es_401(ventas):
    assert APIClient().post("/api/forecast", {"product_id": PRODUCT_ID}, format="json").status_code == 401