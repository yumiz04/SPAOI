from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.core.views import PingView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/token", TokenObtainPairView.as_view()),
    path("api/auth/refresh", TokenRefreshView.as_view()),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/ping", PingView.as_view()),
    path("api/", include("apps.products.urls")),
    path("api/", include("apps.inventory.urls")),
path("api/", include("apps.sales.urls")),
    path("api/", include("apps.purchasing.urls")),
    path("api/", include("apps.lots.urls")),
    path("api/", include("apps.risk_config.urls")),
    path("api/", include("apps.analytics.urls")),
    path("api/", include("apps.alerts.urls")),
    path("api/", include("apps.forecasting.urls")),
    path("api/", include("apps.recommendations.urls")),
    path("api/", include("apps.dashboard.urls")),
    path("api/", include("apps.agent.urls")),
]
