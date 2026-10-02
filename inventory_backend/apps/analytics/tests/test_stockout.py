import datetime

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.analytics.analyzers.stockout import StockoutAnalyzer
from apps.core.dates import as_of_date
from apps.inventory.models import Location, ProductInventory
from apps.products.models import Product
from apps.purchasing.models import ProductVendor, PurchaseOrderDetail, PurchaseOrderHeader, Vendor
from apps.sales.models import SalesOrderDetail, SalesOrderHeader

AS_OF = as_of_date()
VENTANA = 90


@pytest.fixture
def catalogo(db):
    """AW con datos minimos y controlados dentro de la ventana de analisis."""
    location = Location.objects.create(id=5, name="Metal Storage")

    critico = Product.objects.create(
        id=1001, name="Critico", product_number="C-1", color="Black",
        safety_stock_level=10, reorder_point=5, standard_cost="10.00", list_price="20.00",
    )
    tranquilo = Product.objects.create(
        id=1002, name="Tranquilo", product_number="T-1", color="Black",
        safety_stock_level=10, reorder_point=5, standard_cost="10.00", list_price="20.00",
    )
    sin_demanda = Product.objects.create(
        id=1003, name="Sin demanda", product_number="S-1", color="Black",
        safety_stock_level=10, reorder_point=5, standard_cost="10.00", list_price="20.00",
    )

    # Critico: 3 dias de cobertura contra 14 de lead time y sin pendientes -> CRITICO.
    ProductInventory.objects.create(
        product=critico, location=location, shelf="A", bin=1, quantity=5,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    # Tranquilo: 1000 unidades contra 5/dia -> cobertura 200 d -> BAJO.
    ProductInventory.objects.create(
        product=tranquilo, location=location, shelf="A", bin=2, quantity=1000,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    ProductInventory.objects.create(
        product=sin_demanda, location=location, shelf="A", bin=3, quantity=50,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )

    vendor = Vendor.objects.create(
        id=1, account_number="V-1", name="Proveedor Uno", credit_rating=5, active_flag=True
    )
    ProductVendor.objects.create(
        product=critico, vendor=vendor, average_lead_time=14, standard_price="10.00",
        min_order_qty=1, max_order_qty=100, on_order_qty=0,
    )
    ProductVendor.objects.create(
        product=tranquilo, vendor=vendor, average_lead_time=14, standard_price="10.00",
        min_order_qty=1, max_order_qty=100, on_order_qty=0,
    )

    inicio = datetime.datetime.combine(AS_OF - datetime.timedelta(days=30), datetime.time(12, 0), tzinfo=datetime.timezone.utc)
    for order_id, product, qty in ((1, critico, 150), (2, tranquilo, 150)):
        header = SalesOrderHeader.objects.create(
            id=order_id,
            order_date=inicio,
            status=5,
        )
        SalesOrderDetail.objects.create(
            order=header, detail_id=order_id, product=product, order_qty=qty,
            unit_price="10.0000",
        )

    return {"critico": critico, "tranquilo": tranquilo, "sin_demanda": sin_demanda}


@pytest.mark.django_db
def test_clasifica_desabasto_critico_con_insumos_en_la_salida(catalogo):
    resultado = {r["product_id"]: r for r in StockoutAnalyzer.run(risk_min="BAJO")}

    critico = resultado[catalogo["critico"].id]
    assert critico["risk"] == "CRITICO"
    # RN-B03: toda recomendacion viene respaldada por los numeros que la producen.
    assert critico["inputs"]["stock"] == 5
    assert critico["inputs"]["daily_demand"] == round(150 / VENTANA, 3)
    assert critico["inputs"]["lead_time_days"] == 14
    assert critico["inputs"]["window_days"] == VENTANA
    assert critico["inputs"]["as_of"] == AS_OF.isoformat()
    assert critico["inputs"]["days_of_cover"] == round(5 / (150 / VENTANA), 1)


@pytest.mark.django_db
def test_producto_con_suficiente_cobertura_queda_bajo(catalogo):
    resultado = {r["product_id"]: r for r in StockoutAnalyzer.run(risk_min="BAJO")}

    tranquilo = resultado[catalogo["tranquilo"].id]
    assert tranquilo["risk"] == "BAJO"
    assert tranquilo["inputs"]["days_of_cover"] > 100


@pytest.mark.django_db
def test_sin_demanda_no_es_riesgo_de_desabasto(catalogo):
    resultado = {r["product_id"]: r for r in StockoutAnalyzer.run(risk_min="BAJO")}

    sin_demanda = resultado[catalogo["sin_demanda"].id]
    assert sin_demanda["risk"] == "BAJO"
    assert sin_demanda["inputs"]["daily_demand"] == 0
    assert sin_demanda["inputs"]["days_of_cover"] is None


@pytest.mark.django_db
def test_risk_min_filtra_resultados(catalogo):
    solo_alto = StockoutAnalyzer.run(risk_min="ALTO")

    assert [r["risk"] for r in solo_alto]
    assert all(r["risk"] in ("CRITICO", "ALTO") for r in solo_alto)


@pytest.mark.django_db
def test_ordenado_por_riesgo_y_limita(catalogo):
    resultado = StockoutAnalyzer.run(risk_min="BAJO", limit=2)

    assert len(resultado) == 2
    assert resultado[0]["risk"] == "CRITICO"


@pytest.mark.django_db
def test_filtrar_un_producto_solo_devuelve_ese(catalogo):
    resultado = StockoutAnalyzer.run(risk_min="BAJO", product_id=catalogo["tranquilo"].id)

    assert len(resultado) == 1
    assert resultado[0]["product_id"] == catalogo["tranquilo"].id


@pytest.mark.django_db
def test_numero_de_consultas_no_crece_con_el_catalogo(catalogo):
    """P4: los calculos se agregan en SQL, no se trae el catalogo a Python."""
    with CaptureQueriesContext(connection) as primera:
        StockoutAnalyzer.run(risk_min="BAJO")

    for i in range(20):
        producto = Product.objects.create(
            id=2000 + i, name="Extra", product_number=f"X-{i}", color="Black",
            safety_stock_level=1, reorder_point=1, standard_cost="1.00", list_price="1.00",
        )
        ProductInventory.objects.create(
            product=producto, location_id=5, shelf="A", bin=9, quantity=7,
            modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
        )

    with CaptureQueriesContext(connection) as segunda:
        StockoutAnalyzer.run(risk_min="BAJO")

    assert len(segunda.captured_queries) <= len(primera.captured_queries) + 1
    assert len(segunda.captured_queries) <= 8