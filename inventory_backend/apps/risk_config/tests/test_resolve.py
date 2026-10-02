import pytest

from apps.risk_config.models import RiskConfig
from apps.risk_config.services import RiskConfigService, RiskParams


@pytest.fixture(autouse=True)
def clear_cache():
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_sin_configuracion_usa_defaults_del_codigo():
    params = RiskConfigService.resolve()

    assert params == RiskParams()
    assert params.expiry_warning_days == 30
    assert params.service_level_z == 1.65


@pytest.mark.django_db
def test_capa_global_se_aplica():
    RiskConfig.objects.create(min_stock=5, expiry_warning_days=45)

    params = RiskConfigService.resolve()

    assert params.min_stock == 5
    assert params.expiry_warning_days == 45
    assert params.analysis_period_days == 90


@pytest.mark.django_db
def test_categoria_gana_a_global():
    RiskConfig.objects.create(min_stock=5, expiry_warning_days=45)
    RiskConfig.objects.create(category_id=7, min_stock=9)

    params = RiskConfigService.resolve(category_id=7)

    assert params.min_stock == 9
    assert params.expiry_warning_days == 45


@pytest.mark.django_db
def test_producto_gana_a_categoria_y_global():
    RiskConfig.objects.create(min_stock=5, expiry_warning_days=45)
    RiskConfig.objects.create(category_id=7, min_stock=9, review_period_days=14)
    RiskConfig.objects.create(product_id=316, min_stock=20)

    params = RiskConfigService.resolve(product_id=316, category_id=7)

    assert params.min_stock == 20
    assert params.review_period_days == 14
    assert params.expiry_warning_days == 45


@pytest.mark.django_db
def test_capa_por_producto_no_contamina_a_otro():
    RiskConfig.objects.create(product_id=316, min_stock=20)

    otro = RiskConfigService.resolve(product_id=999)

    assert otro.min_stock is None


@pytest.mark.django_db
def test_campos_decimales_se_devuelven_como_float():
    RiskConfig.objects.create(low_turnover_threshold="0.5", service_level_z="2.33")

    params = RiskConfigService.resolve()

    assert isinstance(params.low_turnover_threshold, float)
    assert params.low_turnover_threshold == 0.5
    assert isinstance(params.service_level_z, float)
    assert params.service_level_z == 2.33


@pytest.mark.django_db
def test_resolve_usa_cache_y_se_invalida_al_guardar():
    RiskConfig.objects.create(min_stock=5)
    assert RiskConfigService.resolve().min_stock == 5

    RiskConfig.objects.filter(product_id=None, category_id=None).update(min_stock=11)
    assert RiskConfigService.resolve().min_stock == 5

    RiskConfigService.invalidate()
    assert RiskConfigService.resolve().min_stock == 11