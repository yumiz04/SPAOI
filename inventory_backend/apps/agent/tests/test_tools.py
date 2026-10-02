import datetime

import pytest

from apps.agent import registry
from apps.agent.models import ToolLog
from apps.alerts.services import AlertService
from apps.core.dates import as_of_date
from apps.inventory.models import Location, ProductInventory
from apps.lots.models import Lot
from apps.products.models import Product
from apps.purchasing.models import ProductVendor, Vendor
from apps.sales.models import SalesOrderDetail, SalesOrderHeader


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
    vendor = Vendor.objects.create(
        id=1, account_number="V-1", name="Proveedor Uno", credit_rating=5, active_flag=True
    )
    ProductVendor.objects.create(
        product=producto, vendor=vendor, average_lead_time=14, standard_price="10.00",
        min_order_qty=1, max_order_qty=100, on_order_qty=0,
    )
    Lot.objects.create(
        product_id=680, location_id=5, lot_number="L-1", quantity=50,
        entry_date=as_of_date() - datetime.timedelta(days=10),
        expiration_date=as_of_date() + datetime.timedelta(days=5),
    )
    inicio = datetime.datetime.combine(
        as_of_date() - datetime.timedelta(days=30), datetime.time(10, 0),
        tzinfo=datetime.timezone.utc,
    )
    header = SalesOrderHeader.objects.create(id=1, order_date=inicio, status=5)
    SalesOrderDetail.objects.create(
        order=header, detail_id=1, product=producto, order_qty=150, unit_price="10.0000"
    )
    return producto


def test_catalogo_contiene_las_19_herramientas():
    assert len(registry.TOOLS) == 19


def test_el_input_schema_es_un_json_schema_de_objeto():
    entrada = {t["name"]: t for t in registry.catalog()}["analizar_desabasto"]

    assert entrada["input_schema"]["type"] == "object"
    assert "riesgo_minimo" in entrada["input_schema"]["properties"]
    assert entrada["mutating"] is False


@pytest.mark.django_db
def test_obtener_existencias_devuelve_stock(datos):
    out = registry.execute("obtener_existencias", {"product_id": 680})

    assert out["success"] is True
    assert out["data"][0]["quantity"] == 120
    assert out["data"][0]["location_id"] == 5


@pytest.mark.django_db
def test_analizar_desabasto_devuelve_lista(datos):
    out = registry.execute("analizar_desabasto", {"riesgo_minimo": "BAJO"})

    assert out["success"] is True
    assert isinstance(out["data"], list)
    assert any(r["product_id"] == 680 for r in out["data"])


@pytest.mark.django_db
def test_analizar_caducidades_devuelve_el_lote(datos):
    out = registry.execute("analizar_caducidades", {"dias": 30})

    assert out["success"] is True
    assert out["data"][0]["lot_number"] == "L-1"


@pytest.mark.django_db
def test_proponer_reposicion_es_una_propuesta(datos):
    out = registry.execute("proponer_reposicion", {"product_id": 680})

    assert out["success"] is True
    assert out["data"][0]["is_proposal"] is True


@pytest.mark.django_db
def test_parametro_invalido_no_es_500(datos):
    out = registry.execute("analizar_desabasto", {"riesgo_minimo": "MALO"})

    assert out["success"] is False
    assert out["code"] == "VALIDATION_ERROR"
    assert out["data"] is None


@pytest.mark.django_db
def test_herramienta_inexistente(datos):
    out = registry.execute("no_existe", {})

    assert out["success"] is False
    assert out["code"] == "TOOL_NOT_FOUND"


@pytest.mark.django_db
def test_error_de_dominio_se_traduce(datos):
    out = registry.execute("proponer_reposicion", {"product_id": 999999})

    assert out["success"] is False
    assert out["code"] == "PRODUCT_NOT_FOUND"


@pytest.mark.django_db
def test_registra_traza_en_tool_log(datos):
    antes = ToolLog.objects.count()

    registry.execute(
        "analizar_desabasto", {"riesgo_minimo": "BAJO"},
        conversation_id="conv-1", user_request="¿qué está en riesgo?",
    )

    assert ToolLog.objects.count() == antes + 1
    traza = ToolLog.objects.latest("id")
    assert traza.tool == "analizar_desabasto"
    assert traza.service_executed == "StockoutAnalyzer.run"
    assert traza.success is True
    assert traza.parameters == {"riesgo_minimo": "BAJO"}
    assert traza.conversation_id == "conv-1"
    assert traza.result_summary == {"count": 1}
    assert traza.execution_time_ms >= 0


@pytest.mark.django_db
def test_registra_error_en_tool_log(datos):
    registry.execute("analizar_desabasto", {"riesgo_minimo": "MALO"})

    traza = ToolLog.objects.latest("id")
    assert traza.success is False
    assert traza.error == "Parámetros inválidos"


@pytest.mark.django_db
def test_analizar_inventario_sin_producto_usa_el_analizador(datos):
    global_ = registry.execute("analizar_inventario", {})
    filtrado = registry.execute("analizar_inventario", {"categoria": 1})

    assert global_["success"] is True
    assert "totals" in global_["data"]
    assert filtrado["success"] is True
    assert isinstance(filtrado["data"]["by_category"], list)


@pytest.mark.django_db
def test_cada_herramienta_ejecuta_con_parametros_validos(datos):
    alerta = AlertService.create(
        product_id=680, alert_type="BAJO_STOCK", severity="MEDIA", message="revisar"
    )
    casos = {
        "buscar_productos": {"texto": "Frame"},
        "obtener_existencias": {"product_id": 680},
        "obtener_lotes": {"product_id": 680},
        "obtener_movimientos": {"product_id": 680},
        "obtener_ventas": {"product_id": 680},
        "obtener_compras": {"product_id": 680},
        "obtener_proveedores": {"product_id": 680},
        "analizar_inventario": {"product_id": 680},
        "analizar_desabasto": {"riesgo_minimo": "BAJO"},
        "analizar_caducidades": {"dias": 30},
        "analizar_sobreinventario": {"limite": 10},
        "analizar_rotacion": {"ventana_dias": 90},
        "pronosticar_demanda": {"product_id": 680, "dias_historicos": 30, "dias_pronostico": 7},
        "estimar_fecha_agotamiento": {"product_id": 680},
        "proponer_reposicion": {"product_id": 680},
        "proponer_redistribucion": {"product_id": 680},
        "obtener_alertas": {"estado": "PENDIENTE"},
        "crear_alerta": {
            "product_id": 680, "tipo": "DESABASTO", "severidad": "ALTA", "mensaje": "urge",
        },
        "atender_alerta": {"alerta_id": alerta.id, "nota": "gestionada"},
    }

    assert set(casos) == set(registry.TOOLS)
    for nombre, params in casos.items():
        out = registry.execute(nombre, params)
        assert out["success"] is True, f"{nombre}: {out}"
