from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


# ══════════════════ USER PROFILE ══════════════════

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('applicant', 'Abituriyent'),
        ('student', 'Talaba'),
        ('professional', 'Mutaxassis'),
    ]
    PLAN_CHOICES = [
        ('ordinary', 'Oddiy'),
        ('premium', 'Premium'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')

    # Role & Plan
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    role_selected = models.BooleanField(default=False)
    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='ordinary')

    # Personal Info
    bio = models.TextField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    language = models.CharField(max_length=5, default='uz', choices=[('uz', "O'zbek"), ('ru', 'Русский'), ('en', 'English')])

    # Academic Info
    direction = models.CharField(max_length=100, blank=True, null=True)  # Fan yo'nalishi
    university = models.CharField(max_length=255, blank=True, null=True)
    faculty = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)  # Kurs yili (1-4)
    graduation_year = models.IntegerField(blank=True, null=True)

    # Applicant specific
    current_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    target_university = models.CharField(max_length=255, blank=True, null=True)
    selected_field = models.CharField(max_length=100, blank=True, null=True)
    major_subject_1 = models.CharField(max_length=100, blank=True, null=True)
    major_subject_2 = models.CharField(max_length=100, blank=True, null=True)
    mandatory_subjects_json = models.JSONField(default=list, blank=True)

    # Skills & Career
    skills_json = models.JSONField(default=list, blank=True)
    cv_file = models.FileField(upload_to='cv_files/', blank=True, null=True)

    # Goals & Interests
    interests = models.TextField(blank=True, null=True)
    short_term_goals = models.TextField(blank=True, null=True)
    long_term_goals = models.TextField(blank=True, null=True)
    goals_json = models.JSONField(default=list, blank=True)

    # AI Planning & Tracking
    daily_plan_json = models.JSONField(default=dict, blank=True)
    daily_tasks_json = models.JSONField(default=list, blank=True)
    task_backlog_json = models.JSONField(default=list, blank=True)

    # Gamification
    energy_score = models.IntegerField(default=100)
    knowledge_precision = models.FloatField(default=0.0)

    # Gov Services (OneID)
    oneid_id = models.CharField(max_length=100, blank=True, null=True)
    verified_pinfl = models.CharField(max_length=14, blank=True, null=True)
    verified_full_name = models.CharField(max_length=255, blank=True, null=True)
    is_verified_oneid = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile for {self.user.username}"

    @property
    def is_premium(self):
        return self.plan == 'premium' or self.user.is_superuser


# Signal to create UserProfile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


# ══════════════════ TASKS (TZ 3.1) ══════════════════

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Past'),
        ('medium', "O'rta"),
        ('high', 'Yuqori'),
        ('urgent', 'Shoshilinch'),
    ]
    STATUS_CHOICES = [
        ('todo', 'Bajarilishi kerak'),
        ('in_progress', 'Jarayonda'),
        ('done', 'Bajarildi'),
        ('cancelled', 'Bekor qilindi'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='todo')
    deadline = models.DateTimeField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


# ══════════════════ SCHEDULE (TZ 3.1) ══════════════════

class Schedule(models.Model):
    TYPE_CHOICES = [
        ('study', 'Dars'),
        ('rest', 'Dam olish'),
        ('personal', 'Shaxsiy'),
        ('work', 'Ish'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='schedules')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    title = models.CharField(max_length=255)
    task_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='study')
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.date} {self.start_time}-{self.end_time}: {self.title}"


# ══════════════════ GOALS (TZ 3.1) ══════════════════

class Goal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    target_date = models.DateField(blank=True, null=True)
    progress = models.IntegerField(default=0)  # 0-100%
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} ({self.progress}%)"


# ══════════════════ CHAT (TZ 3.2) ══════════════════

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default="New chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} ({self.user.username})"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    context = models.JSONField(default=dict, blank=True)  # RAG kontekst (hujjat bo'laklari)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


# ══════════════════ KNOWLEDGE BASE (TZ 3.3) ══════════════════

class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book')

    def __str__(self):
        return self.name


class UserDocument(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Yuklandi'),
        ('processing', 'Tahlil qilinmoqda'),
        ('indexed', 'Indekslandi'),
        ('error', 'Xatolik'),
    ]
    FILE_TYPE_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
        ('txt', 'TXT'),
        ('md', 'Markdown'),
        ('image', 'Rasm'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='user_docs/')
    title = models.CharField(max_length=255, blank=True)
    file_type = models.CharField(max_length=10, choices=FILE_TYPE_CHOICES, default='pdf')
    file_size = models.IntegerField(default=0)  # Baytlarda
    page_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    summary = models.TextField(blank=True, null=True)
    tags = models.JSONField(default=list, blank=True)
    vector_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title or self.file.name


# ══════════════════ CAREER HUB (TZ 3.4) ══════════════════

class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, default='')
    salary_min = models.IntegerField(blank=True, null=True)
    salary_max = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, default='')
    required_skills = models.JSONField(default=list, blank=True)
    source_url = models.URLField(blank=True, null=True)
    posted_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-posted_at']

    def __str__(self):
        return f"{self.title} @ {self.company}"


class JobMatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_matches')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='matches')
    score = models.FloatField(default=0.0)  # 0.0 - 1.0
    matched_skills = models.JSONField(default=list, blank=True)
    gap_skills = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'job')
        ordering = ['-score']

    def __str__(self):
        return f"{self.user.username} → {self.job.title}: {self.score:.0%}"


# ══════════════════ EDUCATION / LMS ══════════════════

class EducationalResource(models.Model):
    RESOURCE_TYPES = [
        ('video', 'Video dars'),
        ('pdf', 'PDF Konspekt'),
        ('link', 'Tashqi Platforma'),
    ]
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='resources')
    title = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=10, choices=RESOURCE_TYPES)
    url = models.URLField(blank=True, null=True)
    file = models.FileField(upload_to='resources/', blank=True, null=True)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.subject.name} - {self.title}"


class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    knowledge_percentage = models.IntegerField(default=0)
    last_test_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    completed_lessons_count = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'subject')

    def __str__(self):
        return f"{self.user.username} - {self.subject.name}: {self.knowledge_percentage}%"


class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    thumbnail = models.ImageField(upload_to='courses/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class SubjectCourse(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


class LMSUnit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.course.title} - {self.title}"


class LMSTest(models.Model):
    unit = models.ForeignKey(LMSUnit, on_delete=models.CASCADE, related_name='tests')
    question = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Test for {self.unit.title}"


# ══════════════════ UNIVERSITY & QUOTAS ══════════════════

class University(models.Model):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=100)
    uni_type = models.CharField(max_length=50, choices=[('state', 'Davlat'), ('private', 'Xususiy'), ('foreign', 'Xalqaro')], default='state')
    website = models.URLField(blank=True, null=True)
    logo = models.ImageField(upload_to='uni_logos/', blank=True, null=True)

    def __str__(self):
        return self.name


class UniversityDepartment(models.Model):
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    grant_quota = models.IntegerField(default=0)
    contract_quota = models.IntegerField(default=0)
    grant_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    contract_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    subjects_json = models.JSONField(default=list)

    def __str__(self):
        return f"{self.university.name} - {self.name}"


# ══════════════════ NOTIFICATIONS ══════════════════

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} for {self.user.username}"


class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    match_score = models.IntegerField()
    link = models.URLField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.title} - {self.match_score}%"


# ══════════════════ AUDIT LOG ══════════════════

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=255)
    path = models.CharField(max_length=500)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} | {self.action} | {self.timestamp}"
