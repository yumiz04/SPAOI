from django.urls import path

from .views import ToolCatalogView, ToolExecuteView

urlpatterns = [
    path("agent/tools", ToolCatalogView.as_view(), name="agent-tools"),
    path("agent/tools/<str:name>/execute", ToolExecuteView.as_view(), name="agent-tool-execute"),
]
