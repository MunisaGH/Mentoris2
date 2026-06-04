from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NoSignupAccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        """
        Ochiq ro'yxatdan o'tishni butunlay yopish.
        Faqat admin tomondan "Super Login/Parol" berilganlar kira oladi.
        """
        return False


class NoSignupSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, sociallogin, request):
        """
        Google OAuth orqali ham faqat tizimda ALLAQACHON mavjud bo'lgan
        foydalanuvchilarga kirish ruxsat etiladi. Yangi account ochilmaydi.
        """
        email = sociallogin.account.extra_data.get('email', '')
        if not email:
            return False
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(email=email).exists()
