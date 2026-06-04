import logging
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

logger = logging.getLogger(__name__)

# Faqat muhim amallarni loglash — performans uchun
AUDIT_METHODS = {'POST', 'PUT', 'DELETE'}
AUDIT_PATHS = {'/admin-panel/', '/accounts/login/', '/accounts/logout/'}
SKIP_PREFIXES = ('/static/', '/media/', '/api/notifications', '/api/sessions/')


class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Statik/media va tez-tez chaqiriladigan API larni filter qilish
        if any(request.path.startswith(prefix) for prefix in SKIP_PREFIXES):
            return None

        # Faqat muhim amallar (POST/DELETE) yoki maxsus sahifalar loglanadi
        if request.method not in AUDIT_METHODS and request.path not in AUDIT_PATHS:
            return None

        user = request.user if request.user.is_authenticated else None

        # IP manzilni olish (REMOTE_ADDR ishonchli, X-Forwarded-For proxy orqali)
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')

        # Amalni tahlil qilish
        action = f"Sahifa ochildi: {request.path}"
        if request.method == "POST":
            action = f"Ma'lumot yuborildi (POST): {request.path}"
        elif request.method == "DELETE":
            action = f"O'chirildi: {request.path}"

        try:
            AuditLog.objects.create(
                user=user,
                action=action,
                path=request.path,
                method=request.method,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            logger.error(f"AuditLog yozishda xatolik: {e}")

        return None
