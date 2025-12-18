import json
from django.http import JsonResponse
from django.core.cache import cache
from django.utils.decorators import decorator_from_middleware

class IdempotencyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method not in ['POST', 'PUT', 'PATCH']:
            return self.get_response(request)

        key = request.headers.get('Idempotency-Key')
        if not key:
            return self.get_response(request)

        cache_key = f"idempotency:{key}"
        cached_response = cache.get(cache_key)

        if cached_response:
            return JsonResponse(cached_response, safe=False)

        # Mark as processing (optional, requires distributed lock to be perfect)
        # Here we just proceed
        
        response = self.get_response(request)

        if 200 <= response.status_code < 300:
            # Check if response is JSON
            if response.get('Content-Type') == 'application/json':
                try:
                    # We need to render the response to get content if it's not already
                    if hasattr(response, 'render') and callable(response.render):
                        response.render()
                    
                    data = json.loads(response.content)
                    cache.set(cache_key, data, timeout=86400)
                except Exception:
                    pass # Not JSON or parse error

        return response
