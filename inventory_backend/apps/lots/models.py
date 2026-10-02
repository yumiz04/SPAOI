from django.db import models


class Lot(models.Model):
    class Status(models.TextChoices):
        ACTIVO = "ACTIVO"
        AGOTADO = "AGOTADO"
        CADUCADO = "CADUCADO"
        BLOQUEADO = "BLOQUEADO"
        ELIMINADO = "ELIMINADO"

    product_id = models.IntegerField(db_index=True)
    location_id = models.SmallIntegerField(db_index=True)
    lot_number = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    entry_date = models.DateField()
    expiration_date = models.DateField(null=True, blank=True, db_index=True)
    status = models.CharField(max_length=15, choices=Status, default=Status.ACTIVO)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lotes"
        constraints = [
            models.UniqueConstraint(
                fields=["product_id", "location_id", "lot_number"],
                name="uq_lote_producto_ubicacion_numero",
            ),
            models.CheckConstraint(
                condition=models.Q(expiration_date__isnull=True)
                | models.Q(expiration_date__gte=models.F("entry_date")),
                name="ck_lote_caducidad_posterior_entrada",
            ),
        ]