from django.urls import path

from .views import (
    DepletionByProductView,
    DepletionView,
    ExpirationView,
    InventoryTotalsView,
    OverstockView,
    StockoutView,
    TurnoverView,
)

urlpatterns = [
    path("analytics/stockout", StockoutView.as_view()),
    path("analytics/depletion", DepletionView.as_view()),
    path("analytics/depletion/<int:product_id>", DepletionByProductView.as_view()),
    path("analytics/turnover", TurnoverView.as_view()),
    path("analytics/overstock", OverstockView.as_view()),
    path("analytics/expiration", ExpirationView.as_view()),
    path("analytics/inventory", InventoryTotalsView.as_view()),
]