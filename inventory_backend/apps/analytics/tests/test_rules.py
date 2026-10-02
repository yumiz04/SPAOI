from apps.analytics.analyzers.rules import (
    classify_expiration,
    classify_stockout,
    classify_turnover,
    depletion_days,
)


def test_stockout_sin_demanda():
    assert classify_stockout(10, 0, 14) == ("BAJO", None)


def test_stockout_stock_cero():
    assert classify_stockout(0, 5, 14)[0] == "CRITICO"


def test_stockout_alto():
    # cobertura 10 d < lead time 14
    assert classify_stockout(50, 5, 14)[0] == "ALTO"


def test_stockout_critico_sin_pendiente():
    # cobertura 4 d < lead/2 = 7 y sin compras pendientes
    assert classify_stockout(20, 5, 14)[0] == "CRITICO"


def test_stockout_pendiente_evita_critico():
    assert classify_stockout(20, 5, 14, pending=100)[0] == "ALTO"


def test_stockout_medio_dentro_de_la_revision():
    # cobertura 15 d: >= lead 14 pero < lead + review 21
    assert classify_stockout(75, 5, 14, review_days=7)[0] == "MEDIO"


def test_stockout_bajo_con_margen():
    riesgo, cover = classify_stockout(500, 5, 14, review_days=7)

    assert riesgo == "BAJO"
    assert cover == 100


def test_stockout_devuelve_la_cobertura():
    _, cover = classify_stockout(50, 5, 14)

    assert cover == 10


def test_rotacion_sin_ventas():
    assert classify_turnover(0, 100, 1, 6)[0] == "SIN_MOVIMIENTO"


def test_rotacion_inventario_cero():
    riesgo, valor = classify_turnover(50, 0, 1, 6)

    assert riesgo == "ALTA_ROTACION"
    assert valor == float("inf")


def test_rotacion_baja():
    riesgo, valor = classify_turnover(50, 100, 1, 6)

    assert riesgo == "BAJA_ROTACION"
    assert valor == 0.5


def test_rotacion_media():
    riesgo, valor = classify_turnover(300, 100, 1, 6)

    assert riesgo == "ROTACION_MEDIA"
    assert valor == 3


def test_rotacion_alta_en_el_umbral():
    # t == high cae en ALTA_ROTACION
    assert classify_turnover(600, 100, 1, 6)[0] == "ALTA_ROTACION"


def test_caducado():
    assert classify_expiration(-1, 30) == "CADUCADO"


def test_caducidad_alta():
    # <= warning/3 = 10 dias
    assert classify_expiration(10, 30) == "ALTO"


def test_caducidad_media():
    assert classify_expiration(30, 30) == "MEDIO"


def test_caducidad_baja():
    assert classify_expiration(31, 30) == "BAJO"


def test_agotamiento_sin_demanda():
    assert depletion_days(100, 0) is None


def test_agotamiento_redondea_hacia_arriba():
    # 100/3 = 33.33 -> 34 dias
    assert depletion_days(100, 3) == 34


def test_agotamiento_exacto():
    assert depletion_days(100, 5) == 20