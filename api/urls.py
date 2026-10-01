from django.urls import path
from .views import HealthCheckView, AIChatView, AnalyticsSummaryView, SchemaDiscoveryView, OpenAPISchemaView

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="api_health"),
    path("chat/", AIChatView.as_view(), name="api_ai_chat"),
    path("analytics/", AnalyticsSummaryView.as_view(), name="api_analytics"),
    path("schema/", SchemaDiscoveryView.as_view(), name="api_schema"),
    path("openapi.json", OpenAPISchemaView.as_view(), name="api_openapi"),
]

