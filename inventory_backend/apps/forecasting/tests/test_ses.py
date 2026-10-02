import pytest

from apps.forecasting.models_ses import ses_confidence, ses_forecast


def test_serie_constante_da_sigma_cero():
    nivel, sigma = ses_forecast([5.0] * 30)

    assert nivel == pytest.approx(5.0)
    assert sigma == 0.0


def test_serie_vacia_devuelve_ceros():
    assert ses_forecast([]) == (0.0, 0.0)


def test_un_solo_dato_no_tiene_errores():
    assert ses_forecast([7.0]) == (7.0, 0.0)


def test_nivel_reacciona_al_ultimo_valor():
    """Con alpha 1 el nivel es exactamente la última observación."""
    nivel, _ = ses_forecast([1.0, 1.0, 1.0, 10.0], alpha=1.0)

    assert nivel == pytest.approx(10.0)


def test_alpha_intermedio_pondera_observacion_y_nivel():
    serie = [0.0, 10.0]
    nivel, _ = ses_forecast(serie, alpha=0.5)

    assert nivel == pytest.approx(5.0)


def test_sigma_crece_con_una_serie_irregular():
    _, sigma_estable = ses_forecast([5.0, 5.0, 5.0, 5.0, 5.0, 5.0])
    _, sigma_irregular = ses_forecast([1.0, 20.0, 3.0, 25.0, 2.0, 22.0])

    assert sigma_estable == 0.0
    assert sigma_irregular > 0.0


def test_confianza_alta_en_serie_estable():
    assert ses_confidence(10.0, 0.0) == pytest.approx(1.0)


def test_confianza_nula_sin_datos():
    assert ses_confidence(0.0, 0.0) == 0.0


def test_confianza_entre_0_y_1():
    for level, sigma in [(10.0, 2.0), (1.0, 10.0), (5.0, 5.0)]:
        c = ses_confidence(level, sigma)
        assert 0.0 <= c <= 1.0