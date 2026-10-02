"""Runner E2E del agente de inventario.

Ejecuta prompts contra el agente real (LLM + tools + API REST) y reporta, por prompt:
  - que herramientas invocó y con qué argumentos
  - si cada tool respondió con éxito (envelope success=True)
  - si la respuesta final es válida
  - latencias y número de resultados

Uso:
    python e2e_runner.py
"""

import json
import pathlib
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import agente
from memoria import SimpleMemory

ROOT = pathlib.Path(__file__).resolve().parent

SCENARIOS = [
    {"prompt": "Busca productos que contengan 'Road'", "expect": ["buscar_productos"]},
    {"prompt": "¿Cuántas existencias hay del producto 680 y en qué ubicaciones?", "expect": ["obtener_existencias"]},
    {"prompt": "Muéstrame los lotes registrados", "expect": ["obtener_lotes"]},
    {"prompt": "Dame los movimientos de inventario del producto 680", "expect": ["obtener_movimientos"]},
    {"prompt": "¿Cuáles son las ventas del producto 680?", "expect": ["obtener_ventas"]},
    {"prompt": "¿Qué órdenes de compra hay para el producto 680?", "expect": ["obtener_compras"]},
    {"prompt": "¿Quiénes son los proveedores del producto 680?", "expect": ["obtener_proveedores"]},
    {"prompt": "Dame un panorama general del inventario", "expect": ["analizar_inventario"]},
    {"prompt": "¿Qué productos tienen riesgo de agotarse?", "expect": ["analizar_desabasto"]},
    {"prompt": "¿Qué lotes están próximos a caducar?", "expect": ["analizar_caducidades"]},
    {"prompt": "¿Qué productos tienen exceso de inventario?", "expect": ["analizar_sobreinventario"]},
    {"prompt": "Analiza la rotación del inventario", "expect": ["analizar_rotacion"]},
    {"prompt": "Pronostica la demanda del producto 680 para los próximos 7 días", "expect": ["pronosticar_demanda"]},
    {"prompt": "¿Cuándo se va a agotar el producto 680?", "expect": ["estimar_fecha_agotamiento"]},
    {"prompt": "¿Qué productos debería reponer primero?", "expect": ["proponer_reposicion", "analizar_desabasto"]},
    {"prompt": "¿Puedo redistribuir inventario del producto 680 entre ubicaciones?", "expect": ["proponer_redistribucion"]},
    {"prompt": "Muéstrame las alertas pendientes", "expect": ["obtener_alertas"]},
    {"prompt": "Crea una alerta de bajo stock para el producto 680 con severidad MEDIA", "expect": ["crear_alerta"]},
    {"prompt": "__ATENDER__", "expect": ["atender_alerta"]},
]


def wrap_tools():
    """Sustituye cada tool del dispatcher por un wrapper que registra la llamada."""

    original = dict(agente._OP)
    calls = []

    def make(name, fn):
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            error = None
            try:
                result = fn(*args, **kwargs)
            except Exception as exc:  # noqa: BLE001
                result = None
                error = f"{type(exc).__name__}: {exc}"
            elapsed = (time.perf_counter() - start) * 1000
            ok = error is None and isinstance(result, dict) and result.get("success", True) is not False
            data = result.get("data") if isinstance(result, dict) else None
            calls.append({
                "name": name,
                "args": kwargs,
                "ok": ok,
                "ms": round(elapsed),
                "items": len(data) if isinstance(data, list) else None,
                "error": error,
            })
            return result

        return wrapper

    for name, fn in original.items():
        agente._OP[name] = make(name, fn)
    return original, calls


def run(prompt):
    original, calls = wrap_tools()
    start = time.perf_counter()
    try:
        answer = agente.responder(SimpleMemory(max_messages=20), prompt)
    except Exception as exc:  # noqa: BLE001
        answer = f"<ERROR: {type(exc).__name__}: {exc}>"
    elapsed = time.perf_counter() - start
    agente._OP.clear()
    agente._OP.update(original)
    return calls, answer, elapsed


def prepare_attender():
    """Crea (o reutiliza) una alerta pendiente y devuelve su id."""

    creada = agente.inventario.crear_alerta(
        product_id=680,
        tipo="AGOTAMIENTO_ESTIMADO",
        severidad="BAJA",
        mensaje="E2E atender alerta",
    )
    if creada.get("success"):
        return creada["data"]["id"]

    pendientes = agente.inventario.obtener_alertas(estado="PENDIENTE").get("data") or []
    if isinstance(pendientes, list) and pendientes:
        return pendientes[0]["id"]
    return None


def main():
    report = []
    for scenario in SCENARIOS:
        prompt = scenario["prompt"]
        if prompt == "__ATENDER__":
            alert_id = prepare_attender()
            if alert_id is None:
                print("[SKIP] Atender alerta: no hay alerta pendiente")
                report.append({
                    "prompt": "Marca como ATENDIDA una alerta",
                    "expect": scenario["expect"],
                    "tools": [],
                    "expected_hit": False,
                    "ok_calls": 0,
                    "answer_ok": False,
                    "answer": "",
                    "seconds": 0.0,
                    "skipped": "no hay alerta pendiente",
                })
                continue
            prompt = f"Marca como ATENDIDA la alerta con id {alert_id}"

        calls, answer, elapsed = run(prompt)
        names = [c["name"] for c in calls]
        hit = any(exp in names for exp in scenario["expect"])
        answer_ok = bool(answer) and "<ERROR" not in str(answer)
        report.append({
            "prompt": prompt,
            "expect": scenario["expect"],
            "tools": calls,
            "expected_hit": hit,
            "ok_calls": sum(1 for c in calls if c["ok"]),
            "answer_ok": answer_ok,
            "answer": str(answer)[:600] if answer else "",
            "seconds": round(elapsed, 2),
        })
        estado = "OK  " if hit and answer_ok else "FAIL"
        print(f"[{estado}] {elapsed:5.1f}s  tools={names or '[]'}  prompt={prompt!r}")

    out = ROOT / "e2e_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    ejecutados = [r for r in report if not r.get("skipped")]
    hits = sum(1 for r in ejecutados if r.get("expected_hit"))
    answers = sum(1 for r in ejecutados if r.get("answer_ok"))
    total_calls = sum(len(r["tools"]) for r in ejecutados)
    ok_calls = sum(r["ok_calls"] for r in ejecutados)
    print(f"\nReporte -> {out}")
    print(
        f"Prompts: {len(ejecutados)} | tool esperada invocada: {hits}/{len(ejecutados)} | "
        f"respuesta válida: {answers}/{len(ejecutados)} | tool calls OK: {ok_calls}/{total_calls}"
    )


if __name__ == "__main__":
    main()
