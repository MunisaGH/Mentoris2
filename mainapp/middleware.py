import logging
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

logger = logging.getLogger(__name__)

class AuditMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Statik fayllarni yoki admin panelning ba'zi yopiq API larini filter qilish mumkin
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        user = request.user if request.user.is_authenticated else None
        
        # IP manzilni olish
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

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
