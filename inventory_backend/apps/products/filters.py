import django_filters as df
from .models import Product


class ProductFilter(df.FilterSet):
    product_id = df.NumberFilter(field_name="id")
    name = df.CharFilter(lookup_expr="icontains")
    product_number = df.CharFilter(lookup_expr="icontains")
    category = df.CharFilter(field_name="subcategory__category__name", lookup_expr="icontains")
    subcategory = df.CharFilter(field_name="subcategory__name", lookup_expr="icontains")

    class Meta:
        model = Product
        fields = []