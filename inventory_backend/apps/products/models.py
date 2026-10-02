from django.db import models


class ProductCategory(models.Model):
    id = models.IntegerField(primary_key=True, db_column="productcategoryid")
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'production"."productcategory'


class ProductSubcategory(models.Model):
    id = models.IntegerField(primary_key=True, db_column="productsubcategoryid")
    category = models.ForeignKey(ProductCategory, models.DO_NOTHING, db_column="productcategoryid",
                                 related_name="subcategories")
    name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'production"."productsubcategory'


class Product(models.Model):
    id = models.IntegerField(primary_key=True, db_column="productid")
    name = models.CharField(max_length=50)
    product_number = models.CharField(max_length=25, db_column="productnumber")
    color = models.CharField(max_length=15, null=True)
    safety_stock_level = models.SmallIntegerField(db_column="safetystocklevel")
    reorder_point = models.SmallIntegerField(db_column="reorderpoint")
    standard_cost = models.DecimalField(max_digits=19, decimal_places=4, db_column="standardcost")
    list_price = models.DecimalField(max_digits=19, decimal_places=4, db_column="listprice")
    subcategory = models.ForeignKey(ProductSubcategory, models.DO_NOTHING, null=True,
                                    db_column="productsubcategoryid", related_name="products")
    sell_end_date = models.DateTimeField(null=True, db_column="sellenddate")
    discontinued_date = models.DateTimeField(null=True, db_column="discontinueddate")

    class Meta:
        managed = False
        db_table = 'production"."product'