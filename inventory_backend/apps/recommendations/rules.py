"""Funciones puras de reposición y redistribución (RF-B16/B17, RN-B04).

Sin BD, sin configuración y sin fechas del sistema: reciben todas las cifras ya
calculadas para poder probarlas en los bordes (sin demanda, sin proveedor, stock 0,
max_qty < necesidad). Las propuestas nunca se persisten como órdenes ni transferencias.
"""

from math import ceil


def replenishment_qty(
    stock, pending, daily_demand, lead_time, review_days, safety_stock, min_qty, max_qty
):
    """Cantidad sugerida de reposición para un producto.

    target = demanda diaria * (lead time + revisión) + stock de seguridad
    La necesidad neta descuenta lo que ya hay (stock) y lo que viene (pending).
    Si supera el máximo del proveedor se recorta y el resto queda como ``remaining_need``.
    """
    target = daily_demand * (lead_time + review_days) + safety_stock
    raw = max(0.0, target - (stock + pending))
    if raw <= 0:
        return {
            "suggested": 0,
            "remaining_need": 0,
            "target_stock": ceil(target),
            "action": "NO_REPONER",
        }
    qty = max(raw, min_qty or 0)
    remaining = 0
    if max_qty and qty > max_qty:
        remaining, qty = qty - max_qty, max_qty
    return {
        "suggested": ceil(qty),
        "remaining_need": ceil(remaining),
        "target_stock": ceil(target),
        "action": "PROPONER_ORDEN",
    }


def propose_transfers(stock_by_loc: dict, daily_demand: float, min_cover: float, max_cover: float):
    """Transferencias propuestas entre ubicaciones del mismo producto.

    Supuesto v1: la demanda se reparte uniforme entre las ubicaciones (d / n). Así
    las coberturas no quedan artificialmente idénticas y sí aparecen traspasos reales.
    Donantes: stock por encima de ``d_i * max_cover``; receptores: por debajo de
    ``d_i * min_cover``.
    """
    n = len(stock_by_loc)
    if n < 2 or daily_demand <= 0:
        return []
    d_i = daily_demand / n
    donors = sorted(
        ((s - d_i * max_cover, loc) for loc, s in stock_by_loc.items() if s > d_i * max_cover),
        reverse=True,
    )
    receivers = sorted(
        ((d_i * min_cover - s, loc) for loc, s in stock_by_loc.items() if s < d_i * min_cover),
        reverse=True,
    )
    transfers, di, ri = [], 0, 0
    donors, receivers = [list(x) for x in donors], [list(x) for x in receivers]
    while di < len(donors) and ri < len(receivers):
        qty = int(min(donors[di][0], receivers[ri][0]))
        if qty > 0:
            transfers.append(
                {"from_location": donors[di][1], "to_location": receivers[ri][1], "quantity": qty}
            )
        donors[di][0] -= qty
        receivers[ri][0] -= qty
        if donors[di][0] < 1:
            di += 1
        if receivers[ri][0] < 1:
            ri += 1
    return transfers
