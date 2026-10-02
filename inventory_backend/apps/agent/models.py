from django.db import models


class ToolLog(models.Model):
    """Traza obligatoria de cada ejecución de herramienta (SRS §27-§28).

    Vive en el esquema propio ``inventory_agent``. Guarda qué se pidió, con qué
    parámetros, cuánto tardó, el servicio real que se ejecutó y si tuvo éxito.
    """

    request_id = models.CharField(max_length=64, db_index=True)
    conversation_id = models.CharField(max_length=64, null=True, db_index=True)
    user_request = models.TextField(null=True)
    tool = models.CharField(max_length=60, db_index=True)
    parameters = models.JSONField()
    service_executed = models.CharField(max_length=120, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    execution_time_ms = models.FloatField()
    success = models.BooleanField()
    error = models.TextField(null=True)
    result_summary = models.JSONField(null=True)

    class Meta:
        db_table = "agent_tool_log"
        ordering = ["-timestamp", "-id"]
        indexes = [
            models.Index(fields=["timestamp"], name="idx_tool_log_timestamp"),
        ]
