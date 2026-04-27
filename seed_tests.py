import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MENTORSUZ.settings')
django.setup()

from mainapp.models import Subject, Course, SubjectCourse, LMSUnit, LMSTest

def seed_tests():
    # 1. Subjects
    math, _ = Subject.objects.get_or_create(name="Matematika", defaults={"icon": "calculate"})
    eng, _ = Subject.objects.get_or_create(name="Ingliz tili", defaults={"icon": "language"})
    
    # 2. Courses
    course_math, _ = Course.objects.get_or_create(title="DTM Matematika 2024", defaults={"description": "Maksimal tayyorgarlik kursi"})
    SubjectCourse.objects.get_or_create(subject=math, course=course_math)
    
    # 3. Units
    unit1, _ = LMSUnit.objects.get_or_create(course=course_math, title="Logarifmik tenglamalar", order=1)
    
    # 4. Tests
    if not unit1.tests.exists():
        LMSTest.objects.create(
            unit=unit1,
            question="log2(x) = 3 bo'lsa, x nechaga teng?",
            option_a="6",
            option_b="8",
            option_c="9",
            option_d="5",
            correct_answer="B",
            explanation="2 ning 3-darajasi 8 ga teng."
        )
        LMSTest.objects.create(
            unit=unit1,
            question="log(100) ning qiymati nechaga teng?",
            option_a="1",
            option_b="10",
            option_c="2",
            option_d="0",
            correct_answer="C",
            explanation="O'nli logarifm asosi 10 ga teng, 10^2 = 100."
        )
        print("Testlar muvaffaqiyatli qo'shildi!")
    else:
        print("Testlar allaqachon mavjud.")

if __name__ == "__main__":
    seed_tests()
