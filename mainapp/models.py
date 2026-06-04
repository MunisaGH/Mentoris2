from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('applicant', 'Abituriyent'),
        ('student', 'Talaba'),
        ('professional', 'Mutaxassis'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Role
    user_role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    role_selected = models.BooleanField(default=False)  # Has user chosen role yet?
    
    # Applicant specific fields
    current_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    target_university = models.CharField(max_length=255, blank=True, null=True)
    selected_field = models.CharField(max_length=100, blank=True, null=True)
    
    # Subject tracking
    major_subject_1 = models.CharField(max_length=100, blank=True, null=True) # Masalan: Matematika
    major_subject_2 = models.CharField(max_length=100, blank=True, null=True) # Masalan: Fizika
    mandatory_subjects_json = models.JSONField(default=list, blank=True) # [Ona tili, Tarix, Mate-majburiy]
    
    # Personal Info (Mandatory)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    
    # AI Planning & Tracking
    daily_plan_json = models.JSONField(default=dict, blank=True)
    daily_tasks_json = models.JSONField(default=list, blank=True) # [{"id": 1, "task": "...", "status": "done/missed"}]
    task_backlog_json = models.JSONField(default=list, blank=True) # "Karzinka"
    
    # Gamification & Quality
    energy_score = models.IntegerField(default=100) # 0-100
    knowledge_precision = models.FloatField(default=0.0) # 0.0-1.0 (Aniq bilim ko'rsatkichi)

    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Academic Info (Optional)
    university = models.CharField(max_length=255, blank=True, null=True)
    faculty = models.CharField(max_length=255, blank=True, null=True)
    major = models.CharField(max_length=255, blank=True, null=True)
    graduation_year = models.IntegerField(blank=True, null=True)
    
    # Professional & Skills
    skills_json = models.JSONField(default=list, blank=True)
    
    # AI Grounding / Goals
    interests = models.TextField(blank=True, null=True)
    short_term_goals = models.TextField(blank=True, null=True)
    long_term_goals = models.TextField(blank=True, null=True)
    
    # Gov Services (OneID foundation)
    oneid_id = models.CharField(max_length=100, blank=True, null=True)
    verified_pinfl = models.CharField(max_length=14, blank=True, null=True)
    verified_full_name = models.CharField(max_length=255, blank=True, null=True)
    is_verified_oneid = models.BooleanField(default=False)

    def __str__(self):
        return f"Profile for {self.user.username}"

# Signal to create UserProfile automatically
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    match_score = models.IntegerField()
    link = models.URLField()
    category = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.title} - {self.match_score}%"

class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default="New chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:30]}..."

class Subject(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='book')

    def __str__(self):
        return self.name

class EducationalResource(models.Model):
    RESOURCE_TYPES = [
        ('video', 'Video dars'),
        ('pdf', 'PDF Konspekt'),
        ('link', 'Tashqi Platforma (Khan Academy/DTM)'),
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
    name = models.CharField(max_length=255)  # Masalan: Iqtisodiyot
    grant_quota = models.IntegerField(default=0)
    contract_quota = models.IntegerField(default=0)
    grant_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0) # O'tgan yilgi ball
    contract_score = models.DecimalField(max_digits=5, decimal_places=1, default=0.0)
    subjects_json = models.JSONField(default=list) # [102, 105] - Subject IDs

    def __str__(self):
        return f"{self.university.name} - {self.name}"


# ══════════════════ LMS ADVANCED STRUCTURE ══════════════════

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
    correct_answer = models.CharField(max_length=1) # A, B, C, D
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Test for {self.unit.title}"


# ══════════════════ RAG & DOCUMENT ANALYSIS ══════════════════

class UserDocument(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'Yuklandi'),
        ('processing', 'Tahlil qilinmoqda'),
        ('indexed', 'Tayyor'),
        ('error', 'Xatolik'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='user_docs/')
    title = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='uploaded')
    vector_id = models.CharField(max_length=255, blank=True, null=True) # Pincone/Chroma ID
    summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title or self.file.name


# ══════════════════ SECURITY & AUDIT (PHASE 1.5) ══════════════════

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

