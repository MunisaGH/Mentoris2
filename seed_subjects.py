import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MENTORSUZ.settings')
django.setup()

from mainapp.models import Subject

subjects = [
    ('Ona tili va adabiyot', 'ona-tili-adabiyot', 'menu_book'),
    ('O\'zbekiston tarixi', 'ozbekiston-tarixi', 'history'),
    ('Biologiya', 'biologiya-subj', 'biotech'),
    ('Kimyo', 'kimyo-subj', 'science'),
    ('Fizika', 'fizika-subj', 'bolt'),
    ('Geografiya', 'geografiya-subj', 'public'),
    ('Rus tili', 'rus-tili', 'language'),
    ('Huquq', 'huquq-subj', 'gavel')
]

for name, slug, icon in subjects:
    obj, created = Subject.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon})
    if created:
        print(f"Created: {name}")
    else:
        print(f"Exists: {name}")
