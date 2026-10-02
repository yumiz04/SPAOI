from django.urls import path

from .views import SalesListView

urlpatterns = [
    path("sales", SalesListView.as_view()),
]
