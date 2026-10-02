from apps.recommendations.rules import propose_transfers, replenishment_qty


def test_sin_necesidad_no_reponer():
    r = replenishment_qty(
        stock=200, pending=0, daily_demand=5, lead_time=14, review_days=7,
        safety_stock=10, min_qty=0, max_qty=0,
    )

    assert r["action"] == "NO_REPONER"
    assert r["suggested"] == 0
    assert r["remaining_need"] == 0


def test_necesidad_bajo_minimo_sube_al_minimo():
    # target = 0.1 * 21 = 2.1 -> raw 2.1 < min 50
    r = replenishment_qty(
        stock=0, pending=0, daily_demand=0.1, lead_time=14, review_days=7,
        safety_stock=0, min_qty=50, max_qty=0,
    )

    assert r["action"] == "PROPONER_ORDEN"
    assert r["suggested"] == 50


def test_necesidad_sobre_maximo_recorta_y_deja_remaining():
    # target = 100 * 21 = 2100; max 100 -> 100 y quedan 2000
    r = replenishment_qty(
        stock=0, pending=0, daily_demand=100, lead_time=14, review_days=7,
        safety_stock=0, min_qty=0, max_qty=100,
    )

    assert r["suggested"] == 100
    assert r["remaining_need"] == 2000


def test_pending_descuenta_la_necesidad():
    r = replenishment_qty(
        stock=0, pending=200, daily_demand=10, lead_time=14, review_days=7,
        safety_stock=0, min_qty=0, max_qty=0,
    )

    # target 210 - 200 = 10
    assert r["suggested"] == 10
    assert r["action"] == "PROPONER_ORDEN"


def test_target_stock_redondea_hacia_arriba():
    r = replenishment_qty(
        stock=0, pending=0, daily_demand=1.5, lead_time=2, review_days=1,
        safety_stock=0, min_qty=0, max_qty=0,
    )

    assert r["target_stock"] == 5


def test_transferencias_sin_demanda_no_propone():
    assert propose_transfers({1: 100, 2: 0}, 0, 7, 30) == []


def test_transferencias_con_una_sola_ubicacion_no_propone():
    assert propose_transfers({1: 100}, 10, 7, 30) == []


def test_transfiere_excedente_del_donante_al_receptor():
    # d_i = 10/2 = 5; donante por encima de 5*30 = 150 -> 150 de exceso
    # receptor por debajo de 5*7 = 35 -> 35 de deficit
    transfers = propose_transfers({1: 300, 2: 0}, 10, 7, 30)

    assert transfers == [{"from_location": 1, "to_location": 2, "quantity": 35}]


def test_reparte_entre_varios_receptores():
    # d_i = 30/3 = 10; donante 1 con exceso, receptores 2 y 3 en deficit
    transfers = propose_transfers({1: 500, 2: 0, 3: 10}, 30, 7, 30)

    receptores = {t["to_location"] for t in transfers}
    assert receptores == {2, 3}
    assert all(t["from_location"] == 1 for t in transfers)
