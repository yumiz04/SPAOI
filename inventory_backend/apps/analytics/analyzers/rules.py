"""Funciones puras de clasificacion: sin BD, sin configuracion, sin fechas del sistema.
Todos los calculos criticos del RN-B02 viven aqui para poder testearlos exhaustivos."""

from math import ceil


def classify_stockout(stock, daily_demand, lead_time, pending=0.0, review_days=7):
    """Devuelve (riesgo, dias_de_cobertura)."""
    if daily_demand <= 0:
        return "BAJO", None  # sin demanda no hay riesgo de desabasto
    if stock <= 0:
        return "CRITICO", 0.0
    cover = stock / daily_demand
    if cover < lead_time / 2 and pending == 0:
        return "CRITICO", cover
    if cover < lead_time:
        return "ALTO", cover
    if cover < lead_time + review_days:
        return "MEDIO", cover
    return "BAJO", cover


def classify_turnover(units_sold, avg_inventory, low, high):
    if units_sold <= 0:
        return "SIN_MOVIMIENTO", 0.0
    if avg_inventory <= 0:
        return "ALTA_ROTACION", float("inf")
    t = units_sold / avg_inventory
    if t < low:
        return "BAJA_ROTACION", t
    if t >= high:
        return "ALTA_ROTACION", t
    return "ROTACION_MEDIA", t


def classify_expiration(days_remaining, warning_days):
    if days_remaining < 0:
        return "CADUCADO"
    if days_remaining <= warning_days / 3:
        return "ALTO"
    if days_remaining <= warning_days:
        return "MEDIO"
    return "BAJO"


def depletion_days(stock, daily_demand):
    return None if daily_demand <= 0 else ceil(stock / daily_demand)