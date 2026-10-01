"""
Automated Integration Tests for Arrendadora Ola Cars AI Superuser Web Portal.
Verifies Login, Initial Loading Splash, Chat, Analytics, and Real ERP Database Analytics.
Enforces Rule 38: Zero dummy or fabricated data.
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

    def test_home_dashboard_real_metrics(self):
        """Verify home dashboard renders real verified ERP metrics from MongoDB."""
        self.client.login(username="admin_test", password="admin123_password")
        response = self.client.get(reverse("dashboard:home"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        
        # Real MongoDB metrics checks
        self.assertIn("1,195,659", content)  # Real total revenue collected ($1,195,659.59)
        self.assertIn("913", content)        # Real active rented vehicles
        self.assertIn("135", content)        # Real total invoices generated
        self.assertIn("5,688.26", content)   # Real overdue balance ($5,688.26)
        self.assertIn("937", content)        # Real total fleet vehicles

    def test_chat_interface_and_real_ajax_api(self):
        """Verify AI chat screen and live JSON chart/table response using real ERP data."""
        self.client.login(username="admin_test", password="admin123_password")
        
        # Check chat UI page
        response = self.client.get(reverse("dashboard:chat"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("AI Assistant", response.content.decode("utf-8"))
        
        # Check AI chat interactive API endpoint with real payment trends
        api_res = self.client.post(
            reverse("dashboard:chat_api"),
            data=json.dumps({"prompt": "Show me real monthly payment trends with a chart"}),
            content_type="application/json"
        )
        self.assertEqual(api_res.status_code, 200)
        data = api_res.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["response_type"], "chart_and_table")
        self.assertIn("chart_data", data)
        self.assertIn("table_data", data)
        self.assertTrue(len(data["table_data"]) >= 5)  # May, Jun, Jul, Aug, Sep

    def test_analytics_interface_real_data(self):
        """Verify analytics screen renders real fleet distribution, invoice generation, and payment trends."""
        self.client.login(username="admin_test", password="admin123_password")
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        
        # Real Payment Trends & Revenue
        self.assertIn("1,195,659", content)
        self.assertIn("Real Payment Trends", content)
        
        # Real Fleet Distribution
        self.assertIn("937", content)  # Total vehicles
        self.assertIn("913", content)  # Active rented
        self.assertIn("SOLUTO", content)  # Kia Soluto (real top model)
        
        # Real Invoice Generation & Collections
        self.assertIn("135", content)       # Invoices count
        self.assertIn("5,688.26", content)  # Overdue balance
        self.assertIn("64.36", content)     # Real collection recovery rate

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
        
        # Logout to check unauthenticated login page in Spanish
        self.client.logout()
        login_res = self.client.get(reverse("dashboard:login") + "?lang=es")
        self.assertEqual(login_res.status_code, 200)
        login_content = login_res.content.decode("utf-8")
        self.assertIn("Bienvenido de Nuevo", login_content)
        self.assertIn("Inicia sesión en tu cuenta de superusuario", login_content)
        self.assertIn("Pregunta. Analiza. Actúa.", login_content)

    def test_analytics_extended_domains(self):
        """
        Verify analytics screen renders all extended ERP domains:
        - Bills & Payables (222 bills, $2.38M billed, $2.11M due)
        - Fixed Assets & Depreciation (685 assets, $10.50M valuation, FA-00475)
        - Bank Accounts & Treasury (17 accounts, $408.6K liquidity, CT 7905)
        - Operating Expenses (2,227 records, $5.21M spend, monthly burn)
        - User Ecosystem & Roles (2,160 drivers, 2,209 customers, RBAC matrix)
        """
        self.client.login(username="admin_test", password="admin123_password")
        response = self.client.get(reverse("dashboard:analytics"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # 1. Bills & Payables
        self.assertIn("222 Bills", content)
        self.assertIn("2,383,657.28", content)
        self.assertIn("2,107,574.59", content)
        self.assertIn("190 bills", content)

        # 2. Fixed Assets & Depreciation
        self.assertIn("685 Units", content)
        self.assertIn("10,504,707.56", content)
        self.assertIn("FA-00475", content)
        self.assertIn("5 Years", content)

        # 3. Bank Accounts & Balances
        self.assertIn("408,622.75", content)
        self.assertIn("Banco General CT 7905", content)
        self.assertIn("367,565.87", content)
        self.assertIn("****7905", content)

        # 4. Operating Expenses
        self.assertIn("5,211,749.86", content)
        self.assertIn("2227 Expense Records", content)
        self.assertIn("331,797.70", content)

        # 5. MongoDB User Ecosystem & AccessControl RBAC
        self.assertIn("4,380", content)  # Total MongoDB Users
        self.assertIn("11 Staff", content)  # Internal Staff across MongoDB collections
        self.assertIn("2,160", content)  # Registered drivers in drivers collection
        self.assertIn("2,209", content)  # Registered customers in customers collection
        self.assertIn("FINANCEADMIN", content)  # MongoDB Role
        self.assertIn("WORKSHOPMANAGER", content)  # MongoDB Role
        self.assertIn("financeadmins", content)  # MongoDB Collection
        self.assertIn("admins", content)  # MongoDB Collection

    def test_ai_chat_extended_domains_queries(self):
        """Verify AI chat assistant provides real data answers for bills, fixed assets, bank accounts, expenses."""
        self.client.login(username="admin_test", password="admin123_password")

        queries = [
            ("Show me vendor bills status and payables", "2,383,657.28"),
            ("What is the valuation of fixed assets and depreciation?", "10,504,707.56"),
            ("What are our bank accounts and cash balances?", "367,565.87"),
            ("Show operating expenses and monthly burn rate", "5,211,749.86"),
            ("Show user role distribution and active drivers", "2,160")
        ]

        for prompt, expected_text in queries:
            res = self.client.post(
                reverse("dashboard:chat_api"),
                data=json.dumps({"prompt": prompt}),
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "success")
            self.assertIn(expected_text, data["message"])

