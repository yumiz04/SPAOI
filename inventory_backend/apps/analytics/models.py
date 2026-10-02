from django.db import models


class AnalysisRecord(models.Model):
    """Trazabilidad de cada ejecucion de analyzer (RN-B05: los analisis se conservan)."""

    analysis_type = models.CharField(max_length=40, db_index=True)
    product_id = models.IntegerField(null=True, db_index=True)
    analysis_date = models.DateTimeField(auto_now_add=True)
    result = models.JSONField()
    parameters = models.JSONField(default=dict)
    algorithm_version = models.CharField(max_length=20)

    class Meta:
        db_table = "analisis"
        ordering = ["-analysis_date", "-id"]