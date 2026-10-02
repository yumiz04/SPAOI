from django.urls import path

from .views import RiskConfigListView, RiskConfigView

urlpatterns = [
    path("risk-config", RiskConfigView.as_view()),
    path("risk-config/layers", RiskConfigListView.as_view()),
]