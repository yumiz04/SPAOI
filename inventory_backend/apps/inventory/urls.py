from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import InventoryListView, InventoryByProductView, LocationViewSet, MovementListView

router = SimpleRouter(trailing_slash=False)
router.register("locations", LocationViewSet, basename="location")

urlpatterns = [
    path("inventory", InventoryListView.as_view()),
    path("inventory/<int:product_id>", InventoryByProductView.as_view()),
    path("movements", MovementListView.as_view()),
]
urlpatterns += router.urls
