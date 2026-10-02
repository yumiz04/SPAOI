from django.db import models


class Alert(models.Model):
    class Type(models.TextChoices):
        DESABASTO = "DESABASTO"
        BAJO_STOCK = "BAJO_STOCK"
        SOBREINVENTARIO = "SOBREINVENTARIO"
        BAJA_ROTACION = "BAJA_ROTACION"
        CADUCIDAD_PROXIMA = "CADUCIDAD_PROXIMA"
        PRODUCTO_CADUCADO = "PRODUCTO_CADUCADO"
        AGOTAMIENTO_ESTIMADO = "AGOTAMIENTO_ESTIMADO"

    class Severity(models.TextChoices):
        BAJA = "BAJA"
        MEDIA = "MEDIA"
        ALTA = "ALTA"
        CRITICA = "CRITICA"

    class Status(models.TextChoices):
        PENDIENTE = "PENDIENTE"
        ATENDIDA = "ATENDIDA"
        DESCARTADA = "DESCARTADA"

    product_id = models.IntegerField(db_index=True)
    location_id = models.SmallIntegerField(null=True, blank=True)
    alert_type = models.CharField(max_length=30, choices=Type)
    severity = models.CharField(max_length=10, choices=Severity)
    message = models.TextField()
    details = models.JSONField(default=dict, blank=True)
    dedup_key = models.CharField(max_length=80)
    status = models.CharField(max_length=12, choices=Status, default=Status.PENDIENTE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "alertas"
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["dedup_key"],
                condition=models.Q(status="PENDIENTE"),
                name="uq_alerta_pendiente_dedup",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "severity"], name="idx_alerta_status_severity"),
            models.Index(fields=["alert_type", "status"], name="idx_alerta_type_status"),
        ]