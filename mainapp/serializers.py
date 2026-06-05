from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserProfile, Task, Schedule, Goal,
    ChatSession, ChatMessage, UserDocument,
    Job, JobMatch, Notification, Subject,
    UserProgress, University, UniversityDepartment,
)


# ══════════════════ AUTH & PROFILE ══════════════════

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    is_premium = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            'user', 'user_role', 'role_selected', 'plan', 'is_premium',
            'bio', 'phone_number', 'birth_date', 'avatar', 'language',
            'direction', 'university', 'faculty', 'major', 'year', 'graduation_year',
            'current_score', 'target_university', 'selected_field',
            'skills_json', 'cv_file',
            'interests', 'short_term_goals', 'long_term_goals',
            'energy_score', 'knowledge_precision',
            'is_verified_oneid', 'verified_full_name', 'verified_pinfl',
        ]
        read_only_fields = ['is_premium', 'energy_score', 'knowledge_precision', 'is_verified_oneid']


# ══════════════════ TASKS ══════════════════

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'priority', 'status',
            'deadline', 'tags', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ══════════════════ SCHEDULE ══════════════════

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = [
            'id', 'date', 'start_time', 'end_time',
            'title', 'task_type', 'description', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


# ══════════════════ GOALS ══════════════════

class GoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Goal
        fields = [
            'id', 'title', 'description', 'target_date',
            'progress', 'is_completed', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# ══════════════════ CHAT ══════════════════

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'context', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class ChatSessionSerializer(serializers.ModelSerializer):
    messages_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'created_at', 'updated_at', 'messages_count', 'last_message']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_messages_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.last()
        return last.content[:100] if last else None


class ChatSessionDetailSerializer(ChatSessionSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta(ChatSessionSerializer.Meta):
        fields = ChatSessionSerializer.Meta.fields + ['messages']


# ══════════════════ DOCUMENTS ══════════════════

class UserDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDocument
        fields = [
            'id', 'title', 'file', 'file_type', 'file_size',
            'page_count', 'status', 'summary', 'tags',
            'vector_id', 'created_at',
        ]
        read_only_fields = ['id', 'file_size', 'page_count', 'status', 'summary', 'vector_id', 'created_at']


# ══════════════════ CAREER ══════════════════

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company', 'location',
            'salary_min', 'salary_max', 'description',
            'required_skills', 'source_url', 'posted_at',
            'is_active', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class JobMatchSerializer(serializers.ModelSerializer):
    job = JobSerializer(read_only=True)
    score_percentage = serializers.SerializerMethodField()

    class Meta:
        model = JobMatch
        fields = ['id', 'job', 'score', 'score_percentage', 'matched_skills', 'gap_skills', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_score_percentage(self, obj):
        return round(obj.score * 100, 1)


# ══════════════════ MISC ══════════════════

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'link', 'is_read', 'created_at']
        read_only_fields = ['id', 'created_at']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'slug', 'description', 'icon']


class UniversitySerializer(serializers.ModelSerializer):
    class Meta:
        model = University
        fields = ['id', 'name', 'location', 'uni_type', 'website']


class UniversityDepartmentSerializer(serializers.ModelSerializer):
    university = UniversitySerializer(read_only=True)

    class Meta:
        model = UniversityDepartment
        fields = ['id', 'university', 'name', 'grant_quota', 'contract_quota', 'grant_score', 'contract_score']
