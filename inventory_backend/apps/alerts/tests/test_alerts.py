import datetime

import pytest
from django.db import IntegrityError, transaction

from apps.alerts.models import Alert
from apps.alerts.services import AlertService
from apps.core.dates import as_of_date
from apps.core.exceptions import AppError
from apps.inventory.models import Location, ProductInventory
from apps.products.models import Product
from apps.sales.models import SalesOrderDetail, SalesOrderHeader

VENTANA = 90


@pytest.fixture
def producto(db):
    location = Location.objects.create(id=5, name="Metal Storage")
    critico = Product.objects.create(
        id=1001, name="Critico", product_number="C-1", color="Black",
        safety_stock_level=10, reorder_point=15, standard_cost="10.00", list_price="20.00",
    )
    ProductInventory.objects.create(
        product=critico, location=location, shelf="A", bin=1, quantity=5,
        modified_date=datetime.datetime(2025, 1, 1, tzinfo=datetime.timezone.utc),
    )
    inicio = datetime.datetime.combine(
        as_of_date() - datetime.timedelta(days=30), datetime.time(12, 0), tzinfo=datetime.timezone.utc
    )
    header = SalesOrderHeader.objects.create(id=1, order_date=inicio, status=5)
    SalesOrderDetail.objects.create(
        order=header, detail_id=1, product=critico, order_qty=150, unit_price="10.0000"
    )
    return critico


# --- dedup -----------------------------------------------------------------

@pytest.mark.django_db
def test_upsert_crea_una_sola_alerta_pendiente(producto):
    _, primera = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "primer aviso", {"stock": 0}
    )
    _, segunda = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.ALTA, "segundo aviso", {"stock": 3}
    )

    assert primera is True
    assert segunda is False
    assert Alert.objects.filter(status=Alert.Status.PENDIENTE).count() == 1

    alerta = Alert.objects.get()
    assert alerta.severity == Alert.Severity.ALTA
    assert alerta.message == "segundo aviso"
    assert alerta.details == {"stock": 3}


@pytest.mark.django_db
def test_dedup_key_incluye_tipo_producto_y_ubicacion():
    assert AlertService.dedup_key(Alert.Type.DESABASTO, 7) == "DESABASTO:7:0"
    assert AlertService.dedup_key(Alert.Type.DESABASTO, 7, 3) == "DESABASTO:7:3"


@pytest.mark.django_db
def test_restriccion_unica_parcial_rechaza_dos_pendientes(producto):
    AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "primero"
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            Alert.objects.create(
                product_id=producto.id, alert_type=Alert.Type.DESABASTO,
                severity=Alert.Severity.CRITICA, message="duplicado",
                dedup_key="DESABASTO:%d:0" % producto.id,
            )


@pytest.mark.django_db
def test_alerta_cerrada_no_bloquea_una_nueva_pendiente(producto):
    alerta, _ = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "primero"
    )
    AlertService.update_status(alerta.id, Alert.Status.ATENDIDA)

    _, creada = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "otro ciclo"
    )

    assert creada is True
    assert Alert.objects.filter(status=Alert.Status.PENDIENTE).count() == 1


# --- estados ---------------------------------------------------------------

@pytest.mark.django_db
def test_actualiza_estado_de_pendiente(producto):
    alerta, _ = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "primero"
    )

    actualizada = AlertService.update_status(alerta.id, Alert.Status.ATENDIDA)

    assert actualizada.status == Alert.Status.ATENDIDA


@pytest.mark.django_db
def test_no_permite_cambiar_el_estado_actual(producto):
    alerta, _ = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "primero"
    )
    AlertService.update_status(alerta.id, Alert.Status.ATENDIDA)

    with pytest.raises(AppError) as exc:
        AlertService.update_status(alerta.id, Alert.Status.DESCARTADA)

    assert exc.value.code == "ALERT_ALREADY_CLOSED"
    assert exc.value.http_status == 409


@pytest.mark.django_db
def test_rechaza_estado_no_valido(producto):
    alerta, _ = AlertService.upsert_from_analysis(
        Alert.Type.DESABASTO, producto.id, Alert.Severity.CRITICA, "primero"
    )

    with pytest.raises(AppError) as exc:
        AlertService.update_status(alerta.id, "PENDIENTE")

    assert exc.value.code == "INVALID_ALERT_STATUS"
    assert exc.value.http_status == 400


@pytest.mark.django_db
def test_alerta_inexistente_da_404(producto):
    with pytest.raises(AppError) as exc:
        AlertService.update_status(999999, Alert.Status.ATENDIDA)

    assert exc.value.http_status == 404


# --- alta manual y filtros -------------------------------------------------

@pytest.mark.django_db
def test_alta_manual_no_duplica_pendiente(producto):
    AlertService.create(producto.id, Alert.Type.BAJO_STOCK, Alert.Severity.MEDIA, "manual")

    with pytest.raises(AppError) as exc:
        AlertService.create(producto.id, Alert.Type.BAJO_STOCK, Alert.Severity.MEDIA, "otro")

    assert exc.value.code == "DUPLICATE_ALERT"
    assert exc.value.http_status == 409


@pytest.mark.django_db
def test_filtros_de_listado(producto):
    for tipo, sev in ((Alert.Type.DESABASTO, Alert.Severity.CRITICA),
                      (Alert.Type.SOBREINVENTARIO, Alert.Severity.BAJA)):
        AlertService.upsert_from_analysis(tipo, producto.id, sev, "msg")

    assert AlertService.list({"type": Alert.Type.DESABASTO}).count() == 1
    assert AlertService.list({"severity": Alert.Severity.BAJA}).count() == 1
    assert AlertService.list({"status": Alert.Status.PENDIENTE}).count() == 2
    assert AlertService.list({"product_id": producto.id}).count() == 2
    assert AlertService.list({"product_id": 4242}).count() == 0
    assert AlertService.list({}).count() == 2


# --- mapeo analyzer -> alerta ---------------------------------------------

@pytest.mark.django_db
def test_mapeo_desabasto_y_agotamiento(producto):
    candidatos = AlertService.build_alerts()
    por_tipo = {c["alert_type"]: c for c in candidatos}

    assert por_tipo[Alert.Type.DESABASTO]["severity"] == Alert.Severity.CRITICA
    assert por_tipo[Alert.Type.BAJO_STOCK]["severity"] == Alert.Severity.MEDIA
    assert por_tipo[Alert.Type.AGOTAMIENTO_ESTIMADO]["severity"] == Alert.Severity.ALTA
    # RN-B03: el mensaje y el details llevan los numeros que justifican la alerta.
    assert por_tipo[Alert.Type.DESABASTO]["details"]["stock"] == 5
    assert por_tipo[Alert.Type.DESABASTO]["details"]["daily_demand"] == round(150 / VENTANA, 3)


@pytest.mark.django_db
def test_solo_desabasto_alto_o_critico_genera_alerta(producto):
    """La tabla del Paso 13 solo mapea CRITICO/ALTO -> DESABASTO."""
    candidatos = [c for c in AlertService.build_alerts()
                  if c["alert_type"] == Alert.Type.DESABASTO]

    assert candidatos
    for c in candidatos:
        assert c["details"]["risk"] in ("CRITICO", "ALTO")
        severidad_esperada = (
            Alert.Severity.CRITICA if c["details"]["risk"] == "CRITICO"
            else Alert.Severity.ALTA
        )
        assert c["severity"] == severidad_esperada


@pytest.mark.django_db
def test_bajo_stock_usa_min_stock_y_punto_de_reorden(producto):
    """disponible = stock - pendientes = 5, por debajo del punto de reorden 15."""
    candidato = next(c for c in AlertService.build_alerts()
                     if c["alert_type"] == Alert.Type.BAJO_STOCK)

    assert candidato["severity"] == Alert.Severity.MEDIA
    assert candidato["details"]["available"] == 5
    assert candidato["details"]["reorder_point"] == 15


@pytest.mark.django_db
def test_no_hay_bajo_stock_si_no_hay_umbrales_configurados(db):
    """Sin min_stock ni punto de reorden no se puede afirmar nada."""
    assert [c for c in AlertService.build_alerts()
            if c["alert_type"] == Alert.Type.BAJO_STOCK] == []