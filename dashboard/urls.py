"""
URL routing for the Ola Cars AI Superuser Dashboard Web Portal.
"""

from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("chat/", views.chat_view, name="chat"),
    path("analytics/", views.analytics_view, name="analytics"),
    path("profile/", views.profile_view, name="profile"),
    path("set-language/", views.set_language_view, name="set_language"),
    path("api/chat/", views.chat_api_endpoint, name="chat_api"),
    path("api/table-data/", views.api_table_pagination_endpoint, name="api_table_pagination"),
]
