from django.db import models


class Location(models.Model):
    id = models.SmallIntegerField(primary_key=True, db_column="locationid")
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'production"."location'


class ProductInventory(models.Model):
    pk = models.CompositePrimaryKey("product_id", "location_id")
    product = models.ForeignKey("products.Product", models.DO_NOTHING,
                                db_column="productid", related_name="inventory")
    location = models.ForeignKey(Location, models.DO_NOTHING,
                                 db_column="locationid", related_name="inventory")
    shelf = models.CharField(max_length=10)
    bin = models.SmallIntegerField()
    quantity = models.SmallIntegerField()
    modified_date = models.DateTimeField(db_column="modifieddate")

    class Meta:
        managed = False
        db_table = 'production"."productinventory'


class TransactionHistory(models.Model):
    """transaction_type: W = orden de trabajo, S = venta, P = compra."""
    id = models.IntegerField(primary_key=True, db_column="transactionid")
    product = models.ForeignKey("products.Product", models.DO_NOTHING, db_column="productid")
    reference_order_id = models.IntegerField(db_column="referenceorderid")
    transaction_date = models.DateTimeField(db_column="transactiondate")
    transaction_type = models.CharField(max_length=1, db_column="transactiontype")
    quantity = models.IntegerField()
    actual_cost = models.DecimalField(max_digits=19, decimal_places=4, db_column="actualcost")

    class Meta:
        managed = False
        db_table = 'production"."transactionhistory'
