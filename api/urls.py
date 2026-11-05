from django.urls import path, re_path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    HealthCheckView, AIChatView, AnalyticsSummaryView, FleetOverviewView, SchemaDiscoveryView,
    OpenAPISchemaView, JWTAuthLoginView, UserProfileView, AuthLoginView, OAuthAuthorizeView, OAuthTokenView,
    RemoteMCPSSEView, RemoteMCPMessagesView, StreamableMCPView
)

urlpatterns = [
    path("", OpenAPISchemaView.as_view(), name="api_root"),
    re_path(r"^mcp/?$", StreamableMCPView.as_view(), name="api_streamable_mcp"),
    
    # JWT Authentication Endpoints
    re_path(r"^auth/jwt/token/?$", JWTAuthLoginView.as_view(), name="api_jwt_token"),
    re_path(r"^auth/jwt/refresh/?$", TokenRefreshView.as_view(), name="api_jwt_refresh"),
    re_path(r"^auth/me/?$", UserProfileView.as_view(), name="api_user_profile"),

    # Legacy & OAuth Endpoints
    re_path(r"^auth/login/?$", AuthLoginView.as_view(), name="api_auth_login"),
    re_path(r"^authorize/?$", OAuthAuthorizeView.as_view(), name="api_oauth_authorize"),
    re_path(r"^token/?$", OAuthTokenView.as_view(), name="api_oauth_token"),
    re_path(r"^mcp/sse/?$", RemoteMCPSSEView.as_view(), name="api_mcp_sse"),
    re_path(r"^mcp/messages/?$", RemoteMCPMessagesView.as_view(), name="api_mcp_messages"),
    
    # Core Analytics APIs
    re_path(r"^health/?$", HealthCheckView.as_view(), name="api_health"),
    re_path(r"^chat/?$", AIChatView.as_view(), name="api_ai_chat"),
    re_path(r"^analytics/?$", AnalyticsSummaryView.as_view(), name="api_analytics"),
    re_path(r"^fleet/?$", FleetOverviewView.as_view(), name="api_fleet"),
    re_path(r"^schema/?$", SchemaDiscoveryView.as_view(), name="api_schema"),
    re_path(r"^openapi\.json/?$", OpenAPISchemaView.as_view(), name="api_openapi"),
]
