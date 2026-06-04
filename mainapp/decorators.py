from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def role_required(allowed_roles=None):
    """
    Foydalanuvchi roli ruxsat etilgan rollar ichida ekanligini tekshiradi.
    Adminlar (Superuser) har doim ruxsatga ega.
    """
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # Adminlarga hamma narsa ruxsat
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Profil yaratilganmi va roli bormi?
            if not hasattr(request.user, 'profile') or not request.user.profile.user_role:
                messages.warning(request, "Iltimos, avval profil ma'lumotlarini to'ldiring.")
                return redirect('complete_profile')

            # Rolni tekshirish
            if request.user.profile.user_role in allowed_roles:
                return view_func(request, *args, **kwargs)
            else:
                messages.error(request, "Ushbu bo'limga kirish uchun ruxsatingiz yo'q.")
                return redirect('dashboard')
        return _wrapped_view
    return decorator
