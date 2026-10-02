from django.db import models


class RiskConfig(models.Model):
    """Parametros de riesgo. product_id/category_id nulos = capa global (RN-B04: todo configurable).

    Todos los parametros ajustables son null=True y SIN default en BD a proposito: NULL
    significa "esta capa no se pronuncia sobre este campo", que es lo que permite que
    producto > categoria > global > defaults del codigo. Si el campo tuviera default en
    BD, una capa de categoria que solo ajusta min_stock pisaria con ese default todos los
    demas valores heredados de la capa global.
    """

    product_id = models.IntegerField(null=True, blank=True)
    category_id = models.IntegerField(null=True, blank=True)
    min_stock = models.PositiveIntegerField(null=True, blank=True)
    expiry_warning_days = models.PositiveIntegerField(null=True, blank=True)
    overstock_days_of_cover = models.PositiveIntegerField(null=True, blank=True)
    analysis_period_days = models.PositiveIntegerField(null=True, blank=True)
    low_turnover_threshold = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )
    high_turnover_threshold = models.DecimalField(
        max_digits=8, decimal_places=3, null=True, blank=True
    )
    service_level_z = models.DecimalField(
        max_digits=4, decimal_places=2, null=True, blank=True
    )
    review_period_days = models.PositiveIntegerField(null=True, blank=True)
    default_lead_time_days = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configuracion_riesgo"
        constraints = [
            models.UniqueConstraint(
                fields=["product_id", "category_id"],
                name="uq_riesgo_producto_categoria",
            )
        ]