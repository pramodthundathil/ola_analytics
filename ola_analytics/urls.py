from django.contrib import admin
from django.urls import path, include
from api.views import HealthCheckView

urlpatterns = [
    path("", HealthCheckView.as_view(), name="root_health"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
]
