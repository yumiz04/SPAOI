import datetime

import pytest

from apps.core.exceptions import NotFoundError
from apps.inventory.models import Location, ProductInventory
from apps.inventory.services import InventoryService
from apps.products.models import Product


@pytest.mark.django_db
class TestInventoryService:
    def setup_method(self):
        self.product = Product.objects.create(
            id=316,
            name="Blade",
            product_number="BL-123",
            color="Black",
            safety_stock_level=100,
            reorder_point=50,
            standard_cost="0.00",
            list_price="0.00",
        )
        self.product_sin_stock = Product.objects.create(
            id=680,
            name="HL Road Frame - Black, 58",
            product_number="FR-123",
            color="Black",
            safety_stock_level=100,
            reorder_point=50,
            standard_cost="0.00",
            list_price="0.00",
        )
        self.loc1 = Location.objects.create(id=5, name="Metal Storage")
        self.loc2 = Location.objects.create(id=10, name="Frame Forming")
        self.loc3 = Location.objects.create(id=50, name="Subassembly")

    def test_by_product_inexistente_lanza_not_found(self):
        with pytest.raises(NotFoundError) as exc:
            InventoryService.by_product(999999)

        assert exc.value.code == "PRODUCT_NOT_FOUND"
        assert exc.value.http_status == 404

    def test_by_product_sin_inventario_devuelve_lista_vacia(self):
        resultado = InventoryService.by_product(680)

        assert resultado["product_id"] == 680
        assert resultado["locations"] == []
        assert resultado["total_quantity"] == 0

    def test_by_product_agrupa_por_ubicacion(self):
        ProductInventory.objects.create(
            pk=(316, 5),
            product=self.product,
            location=self.loc1,
            shelf="A",
            bin=11,
            quantity=532,
            modified_date=datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc),
        )
        ProductInventory.objects.create(
            pk=(316, 10),
            product=self.product,
            location=self.loc2,
            shelf="B",
            bin=1,
            quantity=388,
            modified_date=datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc),
        )
        ProductInventory.objects.create(
            pk=(316, 50),
            product=self.product,
            location=self.loc3,
            shelf="B",
            bin=8,
            quantity=441,
            modified_date=datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc),
        )

        resultado = InventoryService.by_product(316)

        assert resultado["product_name"] == "Blade"
        assert resultado["total_quantity"] == 1361
        assert len(resultado["locations"]) == 3

    def test_stock_totals_suma_todas_las_ubicaciones(self):
        ProductInventory.objects.create(
            pk=(316, 5),
            product=self.product,
            location=self.loc1,
            shelf="A",
            bin=11,
            quantity=100,
            modified_date=datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc),
        )
        ProductInventory.objects.create(
            pk=(316, 10),
            product=self.product,
            location=self.loc2,
            shelf="B",
            bin=1,
            quantity=200,
            modified_date=datetime.datetime(2014, 1, 1, tzinfo=datetime.timezone.utc),
        )

        totales = InventoryService.stock_totals()

        assert totales[316] == 300
