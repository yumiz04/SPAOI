"""El agente no toca la BD: las tools solo pueden importar services/analyzers/repositorios.

Revisión estática con ``ast``: falla si algún archivo de ``apps/agent/tools`` importa
``django.db`` o un módulo ``models``. Así se impide que una tool ejecute SQL o consulte
el ORM directamente y se salte la capa de servicios (SRS §11.1).
"""

import ast
import pathlib

FORBIDDEN_EXACT = {"django.db", "django.db.connection"}


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            yield node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name


def _is_forbidden(module: str) -> bool:
    if module in FORBIDDEN_EXACT or module.startswith("django.db."):
        return True
    return module.endswith(".models") or ".models." in module


def test_tools_no_acceden_a_bd():
    archivos = list(pathlib.Path("apps/agent/tools").glob("*.py"))
    assert archivos, "no se encontraron módulos de tools"
    for archivo in archivos:
        for module in _imports(archivo):
            assert not _is_forbidden(module), f"{archivo}: importa {module}"


def test_ninguna_tool_importa_los_modelos_del_agente():
    for archivo in pathlib.Path("apps/agent/tools").glob("*.py"):
        for module in _imports(archivo):
            assert module != "apps.agent.models", f"{archivo}: importa {module}"
