from django.urls import path

from .views import PurchaseListView, SupplierListView

urlpatterns = [
    path("purchases", PurchaseListView.as_view()),
    path("suppliers", SupplierListView.as_view()),
]
