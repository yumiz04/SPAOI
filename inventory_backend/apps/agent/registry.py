"""Registro de herramientas del agente (SRS §11).

Las tools NO acceden a la BD ni a los modelos: solo llaman a services/analyzers.
La entrada se valida con pydantic, que también genera el JSON Schema que se publica
en el catálogo. ``execute`` nunca deja escapar una excepción: la convierte en un
envelope ``success: false`` con ``code`` y ``message`` y deja traza en ``ToolLog``.
"""

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Callable

from pydantic import BaseModel, ValidationError

from apps.core.exceptions import AppError
from .models import ToolLog

logger = logging.getLogger(__name__)


@dataclass
class ToolSpec:
    name: str
    description: str
    input_model: type[BaseModel]
    fn: Callable
    service: str
    mutating: bool = False
    errors: tuple = ()


TOOLS: dict[str, ToolSpec] = {}


def agent_tool(*, name, description, input_model, service, mutating=False, errors=()):
    def deco(fn):
        TOOLS[name] = ToolSpec(name, description, input_model, fn, service, mutating, tuple(errors))
        return fn

    return deco


def catalog():
    return [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.input_model.model_json_schema(),
            "errors": list(t.errors),
            "mutating": t.mutating,
        }
        for t in TOOLS.values()
    ]


def _summary(data):
    if isinstance(data, dict):
        return {"keys": list(data.keys())}
    if isinstance(data, list):
        return {"count": len(data)}
    return None


def execute(name, raw_params, *, user=None, conversation_id=None, user_request=None):
    spec = TOOLS.get(name)
    if not spec:
        return {
            "success": False,
            "data": None,
            "message": f"Herramienta '{name}' no existe",
            "code": "TOOL_NOT_FOUND",
        }
    started = time.perf_counter()
    try:
        params = spec.input_model(**(raw_params or {})).model_dump(exclude_none=True)
        out = {"success": True, "data": spec.fn(**params), "message": None}
    except ValidationError as e:
        out = {
            "success": False,
            "data": None,
            "message": "Parámetros inválidos",
            "code": "VALIDATION_ERROR",
            "details": e.errors(include_url=False, include_context=False),
        }
    except AppError as e:
        out = {"success": False, "data": None, "message": e.message, "code": e.code}
    except Exception:  # noqa: BLE001 - el LLM nunca recibe una excepción cruda
        logger.exception("Tool %s falló", name)
        out = {"success": False, "data": None, "message": "Error interno", "code": "INTERNAL_ERROR"}

    ToolLog.objects.create(
        request_id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        user_request=user_request,
        tool=name,
        parameters=raw_params or {},
        service_executed=spec.service,
        execution_time_ms=(time.perf_counter() - started) * 1000,
        success=out["success"],
        error=None if out["success"] else out.get("message"),
        result_summary=_summary(out.get("data")),
    )
    return out
