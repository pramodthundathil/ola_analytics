from django.contrib import admin
from django.urls import path, re_path, include
from api.views import (
    HealthCheckView, OAuthAuthorizeView, OAuthTokenView,
    OpenAPISchemaView, SchemaDiscoveryView, AIChatView,
    AnalyticsSummaryView, RemoteMCPSSEView, RemoteMCPMessagesView, StreamableMCPView
)

urlpatterns = [
    path("", HealthCheckView.as_view(), name="root_health"),
    path("admin/", admin.site.urls),
    
    # Streamable HTTP MCP Route (Recommended by Anthropic Claude Docs)
    re_path(r"^mcp/?$", StreamableMCPView.as_view(), name="root_mcp_streamable"),

    # OAuth 2.0 Authorization Code Flow Routes
    re_path(r"^authorize/?$", OAuthAuthorizeView.as_view(), name="root_oauth_authorize"),
    re_path(r"^token/?$", OAuthTokenView.as_view(), name="root_oauth_token"),
    re_path(r"^oauth/authorize/?$", OAuthAuthorizeView.as_view(), name="root_oauth_authorize_alt"),
    re_path(r"^oauth/token/?$", OAuthTokenView.as_view(), name="root_oauth_token_alt"),

    # Anthropic Remote MCP Protocol Routes
    re_path(r"^sse/?$", RemoteMCPSSEView.as_view(), name="root_mcp_sse"),
    re_path(r"^messages/?$", RemoteMCPMessagesView.as_view(), name="root_mcp_messages"),
    re_path(r"^mcp/sse/?$", RemoteMCPSSEView.as_view(), name="root_mcp_sse_alt"),
    re_path(r"^mcp/messages/?$", RemoteMCPMessagesView.as_view(), name="root_mcp_messages_alt"),

    # Direct Root API shortcuts
    re_path(r"^schema/?$", SchemaDiscoveryView.as_view(), name="root_schema"),
    re_path(r"^openapi\.json/?$", OpenAPISchemaView.as_view(), name="root_openapi"),
    re_path(r"^chat/?$", AIChatView.as_view(), name="root_chat"),
    re_path(r"^health/?$", HealthCheckView.as_view(), name="root_health_alt"),
    re_path(r"^analytics/?$", AnalyticsSummaryView.as_view(), name="root_analytics"),
    
    # API v1 prefix
    path("api/v1/", include("api.urls")),
]
