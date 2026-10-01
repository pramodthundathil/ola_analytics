"""
Automated Integration Tests for Arrendadora Ola Cars AI Superuser Web Portal.
Verifies Login, Initial Loading Splash, Chat, Analytics, and Bilingual Localization.
"""

from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
import json


class DashboardInterfaceTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            username="admin_test",
            email="admin@olacars.com",
            password="admin123_password"
        )
        self.user.role = "SUPERUSER"
        self.user.first_name = "Admin"
        self.user.language_preference = "en"
        self.user.save()

    def test_login_page_renders_splash_loading(self):
        """Verify the login screen renders the initial server startup loading animation."""
        response = self.client.get(reverse("dashboard:login"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        
        # Check initial loading screen elements
        self.assertIn("server-startup-splash", content)
        self.assertIn("splash-neon-ring", content)
        self.assertIn("Initializing Ola Cars AI Engine...", content)
        
        # Check Arrendadora Ola Cars branding and login form
        self.assertIn("ARRENDADORA", content)
        self.assertIn("LA CARS", content)
        self.assertIn("Welcome Back", content)
        self.assertIn("Quick Demo Credentials", content)

    def test_login_authentication_success(self):
        """Verify login authenticates and sets session & language cookie."""
        response = self.client.post(reverse("dashboard:login"), {
            "username": "admin@olacars.com",
            "password": "admin123_password"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:home"))
        self.assertIn("ola_lang", response.cookies)

    def test_home_dashboard_metrics(self):
        """Verify home dashboard renders key metrics and quick questions."""
        self.client.login(username="admin_test", password="admin123_password")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        
        # Key metrics check
        self.assertIn("2,648", content)
        self.assertIn("428", content)
        self.assertIn("$186,450", content)
        self.assertIn("$42,300", content)
        self.assertIn("Quick Questions", content)

    def test_chat_interface_and_ajax_api(self):
        """Verify AI chat screen and live JSON chart/table response."""
        self.client.login(username="admin_test", password="admin123_password")
        
        # Check chat UI page
        response = self.client.get(reverse("dashboard:chat"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI Assistant", response.content.decode("utf-8"))
        
        # Check AI chat interactive API endpoint
        api_res = self.client.post(
            reverse("dashboard:chat_api"),
            data=json.dumps({"prompt": "Show me monthly revenue for the last 6 months with a chart"}),
            content_type="application/json"
        )
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["response_type"], "chart_and_table")
        self.assertIn("chart_data", data)
        self.assertIn("table_data", data)
        self.assertEqual(len(data["table_data"]), 6)

    def test_analytics_interface(self):
        """Verify analytics screen renders revenue trend, vehicle donut, and fleet overview."""
        self.client.login(username="admin_test", password="admin123_password")
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        
        self.assertIn("Revenue Trend", content)
        self.assertIn("$1,203,880", content)
        self.assertIn("Bookings by Vehicle Type", content)
        self.assertIn("Toyota Fortuner", content)
        self.assertIn("Fleet Overview", content)
        self.assertIn("824", content)  # Total vehicles

    def test_bilingual_spanish_localization(self):
        """Verify seamless switching to Spanish language across the UI."""
        self.client.login(username="admin_test", password="admin123_password")
        
        # Switch language to Spanish (es)
        switch_res = self.client.get(reverse("dashboard:set_language") + "?lang=es")
        self.assertEqual(switch_res.status_code, 302)
        
        # Check that pages are translated to Spanish
        home_res = self.client.get(reverse("dashboard:home"))
        home_content = home_res.content.decode("utf-8")
        self.assertIn("Bienvenido", home_content)
        self.assertIn("Preguntas Rápidas", home_content)
        self.assertIn("Reservas Totales", home_content)
        self.assertIn("Ingresos Totales", home_content)
        
        # Logout to check unauthenticated login page in Spanish
        self.client.logout()
        login_res = self.client.get(reverse("dashboard:login") + "?lang=es")
        self.assertEqual(login_res.status_code, 200)
        login_content = login_res.content.decode("utf-8")
        self.assertIn("Bienvenido de Nuevo", login_content)
        self.assertIn("Inicia sesión en tu cuenta de superusuario", login_content)
        self.assertIn("Pregunta. Analiza. Actúa.", login_content)
