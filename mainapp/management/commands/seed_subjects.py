from django.core.management.base import BaseCommand
from mainapp.models import Subject


class Command(BaseCommand):
    help = "Fanlar (Subject) bazasini boshlang'ich ma'lumotlar bilan to'ldiradi"

    def handle(self, *args, **options):
        subjects = [
            ('Ona tili va adabiyot', 'ona-tili-adabiyot', 'menu_book'),
            ("O'zbekiston tarixi", 'ozbekiston-tarixi', 'history'),
            ('Biologiya', 'biologiya-subj', 'biotech'),
            ('Kimyo', 'kimyo-subj', 'science'),
            ('Fizika', 'fizika-subj', 'bolt'),
            ('Geografiya', 'geografiya-subj', 'public'),
            ('Rus tili', 'rus-tili', 'language'),
            ('Huquq', 'huquq-subj', 'gavel'),
        ]

        for name, slug, icon in subjects:
            obj, created = Subject.objects.get_or_create(
                slug=slug, defaults={'name': name, 'icon': icon}
            )
            status = "Yaratildi" if created else "Mavjud"
            self.stdout.write(f"  {status}: {name}")

        self.stdout.write(self.style.SUCCESS("Fanlar bazasi muvaffaqiyatli yangilandi!"))
