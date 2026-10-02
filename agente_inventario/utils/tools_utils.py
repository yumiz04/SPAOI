import functools


def _safe(fn):
    """Convierte errores de validación o de red en respuestas {'success': False}."""

    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return fn(self, *args, **kwargs)
        except ValueError as error:
            return {"success": False, "error": str(error)}

    return wrapper
