from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Count, Q
from datetime import date

from .models import (
    UserProfile, Task, Schedule, Goal,
    ChatSession, ChatMessage, UserDocument,
    Job, JobMatch, Notification, Subject,
)
from .serializers import (
    UserProfileSerializer, TaskSerializer, ScheduleSerializer, GoalSerializer,
    ChatSessionSerializer, ChatSessionDetailSerializer, ChatMessageSerializer,
    UserDocumentSerializer, JobSerializer, JobMatchSerializer,
    NotificationSerializer, SubjectSerializer, UserSerializer,
)


# ══════════════════ PERMISSIONS ══════════════════

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


# ══════════════════ PROFILE ══════════════════

class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = UserProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


# ══════════════════ TASKS (TZ 3.1) ══════════════════

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'priority']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'deadline', 'priority']

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ══════════════════ SCHEDULE (TZ 3.1) ══════════════════

class ScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['date', 'task_type']

    def get_queryset(self):
        return Schedule.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ══════════════════ GOALS (TZ 3.1) ══════════════════

class GoalViewSet(viewsets.ModelViewSet):
    serializer_class = GoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Goal.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# ══════════════════ DAILY DASHBOARD (TZ 3.1) ══════════════════

class DailyDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        today = date.today()
        user = request.user

        # Bugungi vazifalar
        tasks = Task.objects.filter(user=user, status__in=['todo', 'in_progress'])
        tasks_data = TaskSerializer(tasks[:10], many=True).data

        # Bugungi jadval
        schedule = Schedule.objects.filter(user=user, date=today)
        schedule_data = ScheduleSerializer(schedule, many=True).data

        # Maqsadlar
        goals = Goal.objects.filter(user=user, is_completed=False)
        goals_data = GoalSerializer(goals[:5], many=True).data

        # Statistika
        stats = {
            'total_tasks': Task.objects.filter(user=user).count(),
            'completed_today': Task.objects.filter(user=user, status='done', updated_at__date=today).count(),
            'pending_tasks': Task.objects.filter(user=user, status='todo').count(),
            'overdue_tasks': Task.objects.filter(user=user, status='todo', deadline__lt=timezone.now()).count(),
        }

        return Response({
            'date': today.isoformat(),
            'tasks': tasks_data,
            'schedule': schedule_data,
            'goals': goals_data,
            'stats': stats,
        })


# ══════════════════ CHAT SESSIONS (TZ 3.2) ══════════════════

class ChatSessionViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ChatSessionDetailSerializer
        return ChatSessionSerializer

    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='send')
    def send_message(self, request, pk=None):
        """Xabar yuborish va AI javob olish"""
        session = self.get_object()
        content = request.data.get('content', '').strip()

        if not content:
            return Response({'error': "Xabar bo'sh bo'lmasligi kerak"}, status=status.HTTP_400_BAD_REQUEST)

        # Foydalanuvchi xabarini saqlash
        user_msg = ChatMessage.objects.create(
            session=session, role='user', content=content
        )

        # AI javob — hozircha placeholder, keyingi bosqichda AI service ulanadi
        try:
            from .services.ai_service import MentorAIService
            ai_service = MentorAIService()
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            history = ChatMessage.objects.filter(session=session).order_by('-timestamp')[:10]
            history_list = [{'role': m.role, 'content': m.content} for m in reversed(history)]

            ai_response = ai_service.get_response(
                user_message=content,
                user_profile=profile,
                chat_history=history_list,
                language=getattr(request, 'LANGUAGE_CODE', 'uz')
            )
        except Exception:
            ai_response = "Kechirasiz, hozir javob qaytarishda muammo yuz berdi."

        assistant_msg = ChatMessage.objects.create(
            session=session, role='assistant', content=ai_response
        )
        session.save()  # updated_at yangilanadi

        return Response({
            'user_message': ChatMessageSerializer(user_msg).data,
            'assistant_message': ChatMessageSerializer(assistant_msg).data,
        })

    @action(detail=True, methods=['get'], url_path='usage')
    def usage(self, request, pk=None):
        """Kunlik limit tekshirish"""
        today = date.today()
        count = ChatMessage.objects.filter(
            session__user=request.user,
            role='user',
            timestamp__date=today,
        ).count()
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        limit = None if profile.is_premium else 20
        return Response({
            'used': count,
            'limit': limit,
            'remaining': (limit - count) if limit else None,
        })


# ══════════════════ DOCUMENTS (TZ 3.3) ══════════════════

class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = UserDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'tags']

    def get_queryset(self):
        return UserDocument.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        file = self.request.FILES.get('file')
        if file:
            ext = file.name.split('.')[-1].lower()
            file_type_map = {'pdf': 'pdf', 'docx': 'docx', 'txt': 'txt', 'md': 'md', 'jpg': 'image', 'png': 'image'}
            serializer.save(
                user=self.request.user,
                file_type=file_type_map.get(ext, 'txt'),
                file_size=file.size,
                title=serializer.validated_data.get('title') or file.name,
            )
        else:
            serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='summarize')
    def summarize(self, request, pk=None):
        """Hujjat xulosa chiqarish"""
        doc = self.get_object()
        # TODO: AI summarization service
        return Response({'summary': doc.summary or 'Xulosa hali tayyorlanmagan.'})

    @action(detail=True, methods=['post'], url_path='query')
    def query(self, request, pk=None):
        """Hujjat bo'yicha savol berish"""
        doc = self.get_object()
        question = request.data.get('question', '')
        # TODO: RAG query service
        return Response({'answer': "Bu funksiya keyingi versiyada qo'shiladi.", 'question': question})


# ══════════════════ CAREER (TZ 3.4) ══════════════════

class JobViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'location']
    search_fields = ['title', 'company', 'description']
    ordering_fields = ['posted_at', 'salary_max']
    queryset = Job.objects.filter(is_active=True)


class CareerMatchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        matches = JobMatch.objects.filter(user=request.user).select_related('job')[:10]
        serializer = JobMatchSerializer(matches, many=True)
        return Response(serializer.data)


class SkillGapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        user_skills = set(profile.skills_json or [])
        matches = JobMatch.objects.filter(user=request.user)

        all_gaps = {}
        for match in matches:
            for skill in (match.gap_skills or []):
                all_gaps[skill] = all_gaps.get(skill, 0) + 1

        sorted_gaps = sorted(all_gaps.items(), key=lambda x: -x[1])
        return Response({
            'user_skills': list(user_skills),
            'gap_skills': [{'skill': s, 'demand_count': c} for s, c in sorted_gaps[:20]],
        })


# ══════════════════ NOTIFICATIONS ══════════════════

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'read'})

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({'status': 'all_read'})


# ══════════════════ ADMIN (TZ 3.6) ══════════════════

class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        from django.contrib.auth.models import User
        today = date.today()

        return Response({
            'total_users': User.objects.count(),
            'active_today': User.objects.filter(last_login__date=today).count(),
            'total_documents': UserDocument.objects.count(),
            'total_chat_messages': ChatMessage.objects.count(),
            'total_tasks': Task.objects.count(),
            'total_jobs': Job.objects.count(),
            'users_by_role': dict(
                UserProfile.objects.values_list('user_role').annotate(count=Count('id')).values_list('user_role', 'count')
            ),
            'users_by_plan': dict(
                UserProfile.objects.values_list('plan').annotate(count=Count('id')).values_list('plan', 'count')
            ),
        })


class AdminUserViewSet(viewsets.ModelViewSet):
    from django.contrib.auth.models import User
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    queryset = User.objects.all()
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
