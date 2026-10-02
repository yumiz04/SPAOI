from datetime import date
from django.conf import settings


def as_of_date() -> date:
    """Única fuente de 'hoy' para todos los análisis."""
    return settings.ANALYSIS_AS_OF_DATE or date.today()