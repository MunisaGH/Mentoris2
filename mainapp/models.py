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
    
    # Personal Info (Mandatory)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
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


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=instance)
    profile.save()

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
    title = models.CharField(max_length=255, default="Yangi suhbat")
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
