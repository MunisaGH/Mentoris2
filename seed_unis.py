import os
import django

# Django muhitini sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MENTORSUZ.settings')
django.setup()

from mainapp.models import University, UniversityDepartment, Subject

def seed_data():
    print("OTM ma'lumotlarini kiritish boshlandi...")
    
    # 1. Universitetlar
    unis = [
        {"name": "Muhammad al-Xorazmiy nomidagi Toshkent axborot texnologiyalari universiteti", "location": "Toshkent", "type": "state"},
        {"name": "O'zbekiston Milliy Universiteti", "location": "Toshkent", "type": "state"},
        {"name": "Westminster International University in Tashkent", "location": "Toshkent", "type": "foreign"},
        {"name": "Toshkent Davlat Iqtisodiyot Universiteti", "location": "Toshkent", "type": "state"},
    ]
    
    for u_data in unis:
        uni, created = University.objects.get_or_create(
            name=u_data["name"],
            defaults={"location": u_data["location"], "uni_type": u_data["type"]}
        )
        
        if created:
            print(f"Yaratildi: {uni.name}")
            
            # 2. Yo'nalishlar (Har bir uni uchun 2 tadan)
            if "axborot texnologiyalari" in uni.name.lower():
                UniversityDepartment.objects.create(
                    university=uni, name="Kompyuter injiniringi",
                    grant_score=180.5, contract_score=145.0,
                    grant_quota=50, contract_quota=150
                )
                UniversityDepartment.objects.create(
                    university=uni, name="Dasturiy injiniring",
                    grant_score=185.2, contract_score=155.0,
                    grant_quota=30, contract_quota=100
                )
            elif "milliy" in uni.name.lower():
                UniversityDepartment.objects.create(
                    university=uni, name="Matematika",
                    grant_score=170.0, contract_score=130.0,
                    grant_quota=40, contract_quota=120
                )
                UniversityDepartment.objects.create(
                    university=uni, name="Fizika",
                    grant_score=165.5, contract_score=125.0,
                    grant_quota=40, contract_quota=120
                )
            elif "international university" in uni.name.lower():
                 UniversityDepartment.objects.create(
                    university=uni, name="Business Information Systems",
                    grant_score=190.0, contract_score=160.0,
                    grant_quota=20, contract_quota=300
                )
            else:
                UniversityDepartment.objects.create(
                    university=uni, name="Iqtisodiyot",
                    grant_score=175.0, contract_score=140.0,
                    grant_quota=35, contract_quota=150
                )

    print("OTM bazasi muvaffaqiyatli yangilandi!")

if __name__ == "__main__":
    seed_data()
