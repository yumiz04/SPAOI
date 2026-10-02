import datetime

import pytest

from apps.analytics.analyzers.inventory import InventoryAnalyzer
from apps.core.dates import as_of_date
from apps.inventory.models import Location, ProductInventory
from apps.products.models import Product, ProductCategory, ProductSubcategory
from apps.sales.models import SalesOrderDetail, SalesOrderHeader

AS_OF = as_of_date()


@pytest.fixture
def catalogo(db):
    categoria = ProductCategory.objects.create(id=1, name="Bikes")
    subcategoria = ProductSubcategory.objects.create(id=10, category=categoria, name="Road Bikes")
    location = Location.objects.create(id=5, name="Metal Storage")

    con_categoria = Product.objects.create(
        id=1001, name="Frame", product_number="F-1", color="Black",
        safety_stock_level=10, reorder_point=5, standard_cost="10.00", list_price="20.00",
        subcategory=subcategoria,
    )
    sin_categoria = Product.objects.create(
        id=1002, name="Wheel", product_number="W-1", color="Black",
        safety_stock_level=1, reorder_point=1, standard_cost="5.00", list_price="8.00",
    )

    ProductInventory.objects.create(
        product=con_categoria, location=location, shelf="A", bin=1, quantity=10,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    ProductInventory.objects.create(
        product=sin_categoria, location=location, shelf="A", bin=2, quantity=4,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )

    inicio = datetime.datetime.combine(
        AS_OF - datetime.timedelta(days=30), datetime.time(12, 0),
        tzinfo=datetime.timezone.utc,
    )
    header = SalesOrderHeader.objects.create(id=1, order_date=inicio, status=5)
    SalesOrderDetail.objects.create(
        order=header, detail_id=1, product=con_categoria, order_qty=90, unit_price="10.0000"
    )
    return {"con_categoria": con_categoria, "sin_categoria": sin_categoria}


@pytest.mark.django_db
def test_run_agrega_totales_y_dias_de_inventario(catalogo):
    out = InventoryAnalyzer.run()

    assert out["totals"]["skus"] == 2
    assert out["totals"]["units"] == 14
    assert out["totals"]["inventory_value"] == pytest.approx(120.0)
    assert out["units_sold_in_window"] == 90
    assert out["window_days"] == 90
    assert out["days_of_inventory"] == pytest.approx(14.0)
    assert out["as_of"] == AS_OF.isoformat()


@pytest.mark.django_db
def test_by_category_agrupa_solo_productos_con_subcategoria(catalogo):
    filas = {f["category_id"]: f for f in InventoryAnalyzer.run()["by_category"]}

    assert list(filas) == [1]
    assert filas[1]["category_name"] == "Bikes"
    assert filas[1]["units"] == 10
    assert filas[1]["value"] == pytest.approx(100.0)
