from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps
import time

def rate_limit(key_prefix, limit=5, period=60):
    """
    Simple rate limiting decorator using Django cache.
    limit: max requests
    period: time window in seconds
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return view_func(request, *args, **kwargs)

            # Adminlarga cheklov yo'q
            if request.user.is_staff:
                return view_func(request, *args, **kwargs)

            key = f"rate_limit:{key_prefix}:{request.user.id}"
            requests = cache.get(key, [])
            
            # Eski so'rovlarni tozalash
            now = time.time()
            requests = [r for r in requests if now - r < period]
            
            if len(requests) >= limit:
                return JsonResponse({
                    "success": False,
                    "error": f"Juda ko'p so'rov yuborildi. Iltimos, {period} soniyadan keyin urinib ko'ring."
                }, status=429)
            
            requests.append(now)
            cache.set(key, requests, period)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
