from django.urls import path, re_path
from .views import HealthCheckView, AIChatView, AnalyticsSummaryView, SchemaDiscoveryView, OpenAPISchemaView, AuthLoginView, OAuthAuthorizeView, OAuthTokenView

urlpatterns = [
    path("", OpenAPISchemaView.as_view(), name="api_root"),
    re_path(r"^auth/login/?$", AuthLoginView.as_view(), name="api_auth_login"),
    re_path(r"^authorize/?$", OAuthAuthorizeView.as_view(), name="api_oauth_authorize"),
    re_path(r"^token/?$", OAuthTokenView.as_view(), name="api_oauth_token"),
    re_path(r"^health/?$", HealthCheckView.as_view(), name="api_health"),
    re_path(r"^chat/?$", AIChatView.as_view(), name="api_ai_chat"),
    re_path(r"^analytics/?$", AnalyticsSummaryView.as_view(), name="api_analytics"),
    re_path(r"^schema/?$", SchemaDiscoveryView.as_view(), name="api_schema"),
    re_path(r"^openapi\.json/?$", OpenAPISchemaView.as_view(), name="api_openapi"),
]
