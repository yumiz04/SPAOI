from django.db import models


class Forecast(models.Model):
    """Un pronóstico por producto y día (inventory_agent.pronosticos)."""
    product_id = models.IntegerField(db_index=True)
    forecast_date = models.DateField()
    forecast_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    model_name = models.CharField(max_length=50)
    model_version = models.CharField(max_length=20)
    confidence = models.DecimalField(max_digits=4, decimal_places=3, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pronosticos"
        ordering = ["forecast_date", "product_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product_id", "forecast_date", "model_name", "model_version"],
                name="uq_pronostico_producto_fecha_modelo",
            ),
        ]
        indexes = [
            models.Index(fields=["product_id", "forecast_date"], name="idx_pronostico_producto_fecha"),
        ]