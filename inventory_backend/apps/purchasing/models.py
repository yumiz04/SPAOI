from django.db import models


class Vendor(models.Model):
    id = models.IntegerField(primary_key=True, db_column="businessentityid")
    account_number = models.CharField(max_length=15, db_column="accountnumber")
    name = models.CharField(max_length=50)
    credit_rating = models.SmallIntegerField(db_column="creditrating")
    active_flag = models.BooleanField(db_column="activeflag")

    class Meta:
        managed = False
        db_table = 'purchasing"."vendor'


class ProductVendor(models.Model):
    pk = models.CompositePrimaryKey("product_id", "vendor_id")
    product = models.ForeignKey("products.Product", models.DO_NOTHING, db_column="productid", related_name="vendors")
    vendor = models.ForeignKey(Vendor, models.DO_NOTHING, db_column="businessentityid", related_name="products")
    average_lead_time = models.IntegerField(db_column="averageleadtime")
    standard_price = models.DecimalField(max_digits=19, decimal_places=4, db_column="standardprice")
    min_order_qty = models.IntegerField(db_column="minorderqty")
    max_order_qty = models.IntegerField(db_column="maxorderqty")
    on_order_qty = models.IntegerField(null=True, db_column="onorderqty")

    class Meta:
        managed = False
        db_table = 'purchasing"."productvendor'


class PurchaseOrderHeader(models.Model):
    """status: 1 Pendiente, 2 Aprobada, 3 Rechazada, 4 Completa."""
    id = models.IntegerField(primary_key=True, db_column="purchaseorderid")
    status = models.SmallIntegerField()
    vendor = models.ForeignKey(Vendor, models.DO_NOTHING, db_column="vendorid")
    order_date = models.DateTimeField(db_column="orderdate")

    class Meta:
        managed = False
        db_table = 'purchasing"."purchaseorderheader'


class PurchaseOrderDetail(models.Model):
    pk = models.CompositePrimaryKey("order_id", "detail_id")
    order = models.ForeignKey(PurchaseOrderHeader, models.DO_NOTHING, db_column="purchaseorderid", related_name="lines")
    detail_id = models.IntegerField(db_column="purchaseorderdetailid")
    product = models.ForeignKey("products.Product", models.DO_NOTHING, db_column="productid")
    due_date = models.DateTimeField(db_column="duedate")
    order_qty = models.SmallIntegerField(db_column="orderqty")
    received_qty = models.DecimalField(max_digits=8, decimal_places=2, db_column="receivedqty")
    rejected_qty = models.DecimalField(max_digits=8, decimal_places=2, db_column="rejectedqty")
    unit_price = models.DecimalField(max_digits=19, decimal_places=4, db_column="unitprice")

    class Meta:
        managed = False
        db_table = 'purchasing"."purchaseorderdetail'
