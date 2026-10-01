"""
Bilingual Translations (English & Spanish) for Arrendadora Ola Cars AI Superuser.
Supports persistent user language preference across web portal and API.
"""

TRANSLATIONS = {
    "en": {
        "brand_subtitle": "ARRENDADORA",
        "brand_name": "OLA CARS",
        "pitch_title": "Ask. Analyze. Act.",
        "pitch_desc": "Your superuser AI assistant for real-time business insights from Ola Cars data.",
        "chat_with_data": "Chat with Data",
        "get_insights": "Get Insights",
        "realtime_info": "Real-time Information",
        
        # Initial Loading & Server Startup
        "server_initializing": "Initializing Ola Cars AI Engine...",
        "connecting_db": "Verifying Read-Only ERP Database Connection...",
        "loading_ready": "System Online • Read-Only Security Active",
        
        # Login
        "welcome_back": "Welcome Back",
        "signin_subtitle": "Sign in to your superuser account",
        "email_address": "Email address",
        "password": "Password",
        "remember_me": "Remember me",
        "forgot_password": "Forgot password?",
        "sign_in": "Sign In",
        "sign_in_sso": "Sign in with SSO",
        "or": "or",
        "demo_accounts": "Quick Demo Credentials",
        "login_failed": "Invalid email or password. Please try again.",
        "admin_demo": "Admin Superuser (admin / admin123)",
        "analyst_demo": "Analyst (analyst / analyst123)",
        
        # Navigation
        "nav_home": "Home",
        "nav_chat": "Chat",
        "nav_analytics": "Analytics",
        "nav_fleet": "Fleet",
        "nav_more": "More",
        "nav_logout": "Logout",
        "theme_toggle": "Toggle Theme",
        "language": "Language",
        
        # Home
        "greeting_admin": "Welcome back, {name}",
        "search_placeholder": "Ask anything about your data...",
        "quick_questions": "Quick Questions",
        "see_all": "See all",
        "todays_bookings": "Today's bookings",
        "monthly_revenue": "Monthly revenue",
        "overdue_customers": "Overdue customers",
        "fleet_utilization": "Fleet utilization",
        "key_metrics": "Key Metrics",
        "this_month": "This Month",
        "total_bookings": "Total Bookings",
        "active_vehicles": "Active Vehicles",
        "total_revenue": "Total Revenue",
        "outstanding": "Outstanding",
        
        # Analytics
        "analytics_title": "Analytics",
        "revenue_trend": "Revenue Trend",
        "bookings_by_type": "Bookings by Vehicle Type",
        "top_vehicles": "Top Performing Vehicles",
        "fleet_overview": "Fleet Overview",
        "total_vehicles": "Total Vehicles",
        "available_vehicles": "Available",
        "rented_vehicles": "Rented",
        "maintenance_vehicles": "Maintenance",
        "inactive_vehicles": "Inactive",
        "utilization_rate": "Utilization Rate",
        "utilization_trend": "Utilization Trend",
        "bookings_count": "{count} bookings",
        "total": "Total",
        
        # Chat
        "ai_assistant_title": "AI Assistant",
        "ai_assistant_subtitle": "Chat with your Ola Cars data",
        "ai_greeting": "Hello! I'm your Ola Cars AI assistant. Ask me anything about your business data. I can show you insights, create charts, find trends, and answer questions from your database in real time.",
        "prompt_last_month": "Show me last month's sales",
        "prompt_overdue": "Which customers are overdue?",
        "prompt_top_vehicles": "Top 10 vehicles by utilization",
        "prompt_revenue_comparison": "Revenue comparison for last 6 months",
        "prompt_new_registrations": "Show me new registrations this week",
        "prompt_chart_revenue": "Show me monthly revenue for the last 6 months with a chart",
        "chat_input_placeholder": "Ask anything about your data...",
        "chat_followup_placeholder": "Ask a follow-up question...",
        "table_month": "Month",
        "table_revenue": "Revenue",
        "table_growth": "Growth",
        "live_query_info": "Live Read-Only Query Executed • 100% ERP Safe",
        "clear_chat": "Clear Chat",
        
        # User Profile / More
        "admin_user": "Admin User",
        "chat_history": "Chat History",
        "saved_reports": "Saved Reports",
        "favorites": "Favorites",
        "custom_queries": "Custom Queries",
        "data_sources": "Data Sources",
        "user_management": "User Management",
        "settings": "Settings",

        # Extended Analytics (Bills, Fixed Assets, Bank Accounts, Expenses, User Roles)
        "vendor_bills": "Vendor Bills & Payables",
        "bills_subtitle": "Accounts payable status & vendor obligations",
        "fixed_assets_title": "Fixed Assets & Depreciation",
        "fixed_assets_subtitle": "Asset registry valuation, useful life & depreciation schedule",
        "bank_accounts_title": "Bank Accounts & Treasury Liquidity",
        "bank_accounts_subtitle": "Real cash positions across operating & reserve accounts",
        "expenses_title": "Operating Expenses & Monthly Burn",
        "expenses_subtitle": "Operating spend patterns & monthly cost burn trends",
        "user_roles_title": "User Ecosystem & RBAC Interactions",
        "user_roles_subtitle": "Audit activity, driver counts & customer directory",
    },
    
    "es": {
        "brand_subtitle": "ARRENDADORA",
        "brand_name": "OLA CARS",
        "pitch_title": "Pregunta. Analiza. Actúa.",
        "pitch_desc": "Tu asistente de IA superusuario para información comercial en tiempo real de Ola Cars.",
        "chat_with_data": "Chatea con los Datos",
        "get_insights": "Obtén Información",
        "realtime_info": "Información en Tiempo Real",
        
        # Initial Loading & Server Startup
        "server_initializing": "Iniciando motor de IA de Ola Cars...",
        "connecting_db": "Verificando conexión segura de sólo lectura con ERP...",
        "loading_ready": "Sistema en Línea • Seguridad de Sólo Lectura Activa",
        
        # Login
        "welcome_back": "Bienvenido de Nuevo",
        "signin_subtitle": "Inicia sesión en tu cuenta de superusuario",
        "email_address": "Correo electrónico",
        "password": "Contraseña",
        "remember_me": "Recordarme",
        "forgot_password": "¿Olvidaste tu contraseña?",
        "sign_in": "Iniciar Sesión",
        "sign_in_sso": "Iniciar sesión con SSO",
        "or": "o",
        "demo_accounts": "Credenciales Rápidas de Demostración",
        "login_failed": "Correo o contraseña incorrectos. Por favor intenta de nuevo.",
        "admin_demo": "Superusuario Admin (admin / admin123)",
        "analyst_demo": "Analista (analyst / analyst123)",
        
        # Navigation
        "nav_home": "Inicio",
        "nav_chat": "Chat IA",
        "nav_analytics": "Analítica",
        "nav_fleet": "Flota",
        "nav_more": "Más",
        "nav_logout": "Cerrar Sesión",
        "theme_toggle": "Cambiar Tema",
        "language": "Idioma",
        
        # Home
        "greeting_admin": "Bienvenido de nuevo, {name}",
        "search_placeholder": "Pregunta lo que sea sobre tus datos...",
        "quick_questions": "Preguntas Rápidas",
        "see_all": "Ver todo",
        "todays_bookings": "Reservas de hoy",
        "monthly_revenue": "Ingresos mensuales",
        "overdue_customers": "Clientes con mora",
        "fleet_utilization": "Utilización de flota",
        "key_metrics": "Métricas Clave",
        "this_month": "Este Mes",
        "total_bookings": "Reservas Totales",
        "active_vehicles": "Vehículos Activos",
        "total_revenue": "Ingresos Totales",
        "outstanding": "Saldo Pendiente",
        
        # Analytics
        "analytics_title": "Analítica",
        "revenue_trend": "Tendencia de Ingresos",
        "bookings_by_type": "Reservas por Tipo de Vehículo",
        "top_vehicles": "Vehículos de Mayor Rendimiento",
        "fleet_overview": "Resumen de Flota",
        "total_vehicles": "Vehículos Totales",
        "available_vehicles": "Disponibles",
        "rented_vehicles": "Alquilados",
        "maintenance_vehicles": "Mantenimiento",
        "inactive_vehicles": "Inactivos",
        "utilization_rate": "Tasa de Utilización",
        "utilization_trend": "Tendencia de Utilización",
        "bookings_count": "{count} reservas",
        "total": "Total",
        
        # Chat
        "ai_assistant_title": "Asistente de IA",
        "ai_assistant_subtitle": "Chatea con tus datos de Ola Cars",
        "ai_greeting": "¡Hola! Soy tu asistente de IA de Ola Cars. Pregúntame lo que desees sobre tus datos empresariales. Puedo mostrarte métricas, generar gráficos, detectar tendencias y responder preguntas de tu base de datos en tiempo real.",
        "prompt_last_month": "Muéstrame las ventas del mes pasado",
        "prompt_overdue": "¿Qué clientes tienen pagos atrasados?",
        "prompt_top_vehicles": "Top 10 vehículos por utilización",
        "prompt_revenue_comparison": "Comparación de ingresos de los últimos 6 meses",
        "prompt_new_registrations": "Muéstrame nuevos registros de esta semana",
        "prompt_chart_revenue": "Muéstrame los ingresos mensuales de los últimos 6 meses con un gráfico",
        "chat_input_placeholder": "Pregunta lo que sea sobre tus datos...",
        "chat_followup_placeholder": "Haz una pregunta de seguimiento...",
        "table_month": "Mes",
        "table_revenue": "Ingresos",
        "table_growth": "Crecimiento",
        "live_query_info": "Consulta en vivo de sólo lectura ejecutada • 100% seguro para ERP",
        "clear_chat": "Limpiar Chat",
        
        # User Profile / More
        "admin_user": "Usuario Administrador",
        "chat_history": "Historial de Chat",
        "saved_reports": "Informes Guardados",
        "favorites": "Favoritos",
        "custom_queries": "Consultas Personalizadas",
        "data_sources": "Fuentes de Datos",
        "user_management": "Gestión de Usuarios",
        "settings": "Configuración",

        # Extended Analytics (Bills, Fixed Assets, Bank Accounts, Expenses, User Roles)
        "vendor_bills": "Facturas de Proveedores y Cuentas por Pagar",
        "bills_subtitle": "Estado de cuentas por pagar y obligaciones con proveedores",
        "fixed_assets_title": "Activos Fijos y Depreciación",
        "fixed_assets_subtitle": "Valoración del registro de activos, vida útil y cronograma de depreciación",
        "bank_accounts_title": "Cuentas Bancarias y Liquidez de Tesorería",
        "bank_accounts_subtitle": "Posiciones de efectivo reales en cuentas operativas y de reserva",
        "expenses_title": "Gastos Operativos y Tasa de Consumo Mensual",
        "expenses_subtitle": "Patrones de gasto operativo y tendencias de costo mensual",
        "user_roles_title": "Ecosistema de Usuarios e Interacciones RBAC",
        "user_roles_subtitle": "Actividad de auditoría, recuento de conductores y directorio de clientes",
    }
}


def get_current_language(request) -> str:
    """Gets the user language from session, cookie, user model or query param, default 'en'."""
    lang = request.GET.get("lang")
    if lang in ["en", "es"]:
        return lang
    
    if hasattr(request, "user") and request.user.is_authenticated and hasattr(request.user, "language_preference"):
        if request.user.language_preference in ["en", "es"]:
            return request.user.language_preference
            
    session_lang = request.session.get("django_language") or request.session.get("language")
    if session_lang in ["en", "es"]:
        return session_lang
        
    cookie_lang = request.COOKIES.get("ola_lang")
    if cookie_lang in ["en", "es"]:
        return cookie_lang
        
    return "en"


def get_translations_for(request) -> dict:
    """Returns the translation dictionary for the active language."""
    lang = get_current_language(request)
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"])
