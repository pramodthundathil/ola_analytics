import os
import sys
from django.apps import AppConfig


class QueryEngineConfig(AppConfig):
    name = "query_engine"

    def ready(self):
        # Skip background prewarm during migrations or test executions
        if any(cmd in sys.argv for cmd in ["test", "makemigrations", "migrate", "collectstatic"]):
            return
        if os.environ.get("RUN_MAIN") == "true" or "runserver" not in sys.argv:
            try:
                from .real_analytics import RealERPAnalytics
                RealERPAnalytics.prewarm_cache_async()
            except Exception:
                pass
