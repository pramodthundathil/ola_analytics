"""
API Key Authentication Module for DRF and Claude / External AI Connectors.
Supports X-API-Key header and Authorization: Bearer <key> header.
"""

import os
from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class APIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        api_key = getattr(settings, "AI_API_KEY", os.getenv("AI_API_KEY", "ola_ai_superuser_key_2026"))

        # Check X-API-Key header
        header_key = request.headers.get("X-API-Key") or request.META.get("HTTP_X_API_KEY")

        # Check Authorization header (Bearer <key> or ApiKey <key>)
        auth_header = request.headers.get("Authorization") or request.META.get("HTTP_AUTHORIZATION", "")
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() in ["bearer", "apikey", "api-key"]:
                header_key = parts[1]

        # If no key provided, allow pass-through
        if not header_key:
            return None

        if header_key != api_key:
            raise AuthenticationFailed("Invalid API Key provided.")

        try:
            user, _ = User.objects.get_or_create(
                username="ai_connector",
                defaults={"email": "ai@olacars.com", "role": "SUPERUSER"}
            )
        except Exception:
            user = None

        return (user, None)
