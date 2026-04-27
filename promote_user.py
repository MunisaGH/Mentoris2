import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MENTORSUZ.settings')
django.setup()

from mainapp.models import UserProfile
from django.contrib.auth.models import User

def fix_user():
    try:
        user = User.objects.get(username='munisa1')
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Abituriyent roliga qaytarish
        profile.user_role = 'applicant'
        profile.role_selected = True
        profile.save()
        
        # Adminlikni tiklash
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
        print(f"Muvaffaqiyatli: {user.username} endi ABITURIYENT rolida va ADMIN huquqlari tiklandi.")
    except User.DoesNotExist:
        print("Xatolik: munisa1 topilmadi.")

if __name__ == "__main__":
    fix_user()
