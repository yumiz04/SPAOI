from django.db import models


class SalesOrderHeader(models.Model):
    id = models.IntegerField(primary_key=True, db_column="salesorderid")
    order_date = models.DateTimeField(db_column="orderdate")
    status = models.SmallIntegerField()

    class Meta:
        managed = False
        db_table = 'sales"."salesorderheader'


class SalesOrderDetail(models.Model):
    pk = models.CompositePrimaryKey("order_id", "detail_id")
    order = models.ForeignKey(SalesOrderHeader, models.DO_NOTHING, db_column="salesorderid", related_name="lines")
    detail_id = models.IntegerField(db_column="salesorderdetailid")
    product = models.ForeignKey("products.Product", models.DO_NOTHING, db_column="productid")
    order_qty = models.SmallIntegerField(db_column="orderqty")
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, db_column="unitprice")

    class Meta:
        managed = False
        db_table = 'sales"."salesorderdetail'
