from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache
from django.views import View

class HealthCheckView(View):
    def get(self, request):
        status = {
            "database": self.check_database(),
            "redis": self.check_redis()
        }
        
        limit_status = 503 if not all(status.values()) else 200
        return JsonResponse(status, status=limit_status)

    def check_database(self):
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except Exception:
            return False

    def check_redis(self):
        try:
            cache.set("health_check", "ok", timeout=1)
            return True
        except Exception:
            return False
