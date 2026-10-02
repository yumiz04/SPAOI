import pytest

from apps.core.exceptions import NotFoundError
from apps.products.models import Product, ProductCategory, ProductSubcategory
from apps.products.services import ProductService


@pytest.fixture
def catalogo(db):
    categoria = ProductCategory.objects.create(id=1, name="Bikes")
    subcategoria = ProductSubcategory.objects.create(id=10, category=categoria, name="Road Bikes")
    Product.objects.create(
        id=680, name="HL Road Frame", product_number="FR-680", color="Black",
        safety_stock_level=500, reorder_point=375, standard_cost="10.00", list_price="20.00",
        subcategory=subcategoria,
    )
    Product.objects.create(
        id=681, name="HL Mountain Frame", product_number="FR-681", color="Black",
        safety_stock_level=500, reorder_point=375, standard_cost="10.00", list_price="20.00",
    )
    return subcategoria


@pytest.mark.django_db
def test_search_por_texto_y_categoria(catalogo):
    por_texto = ProductService.search(texto="Road")
    assert [p["product_id"] for p in por_texto] == [680]
    assert por_texto[0]["category_id"] == 1

    por_categoria = ProductService.search(categoria=1)
    assert [p["product_id"] for p in por_categoria] == [680]


@pytest.mark.django_db
def test_search_respeta_el_limite(catalogo):
    assert len(ProductService.search(texto="Frame", limite=1)) == 1


@pytest.mark.django_db
def test_get_devuelve_producto(catalogo):
    assert ProductService.get(680).name == "HL Road Frame"


@pytest.mark.django_db
def test_get_inexistente(catalogo):
    with pytest.raises(NotFoundError):
        ProductService.get(999999)


@pytest.mark.django_db
def test_get_id_no_numerico(catalogo):
    with pytest.raises(NotFoundError):
        ProductService.get("abc")
