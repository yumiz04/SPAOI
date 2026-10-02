from statistics import pstdev


def ses_forecast(series: list[float], alpha: float = 0.3):
    """Suavizamiento exponencial simple.

    Devuelve (nivel, sigma_de_errores). El pronóstico plano de cada día es el nivel.
    """
    if not series:
        return 0.0, 0.0
    level, errors = series[0], []
    for y in series[1:]:
        errors.append(y - level)
        level = alpha * y + (1 - alpha) * level
    return level, (pstdev(errors) if len(errors) > 1 else 0.0)


def ses_confidence(level: float, sigma: float) -> float:
    """Heurística de confianza en [0, 1].

    Cuanto más estable es la serie (sigma pequeña frente al nivel), más cerca de 1.
    No es una probabilidad calibrada: es un indicador comparable entre productos.
    """
    base = level + sigma
    if base <= 0:
        return 0.0
    return max(0.0, min(1.0, 1 - sigma / base))