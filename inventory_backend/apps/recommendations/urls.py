from django.urls import path

from .views import RedistributionView, ReplenishmentView

urlpatterns = [
    path("recommendations/replenishment", ReplenishmentView.as_view()),
    path("recommendations/redistribution", RedistributionView.as_view()),
]
