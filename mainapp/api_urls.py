from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views
from . import api_views

# ══════════════════ DRF Router ══════════════════
router = DefaultRouter()
router.register(r'tasks', api_views.TaskViewSet, basename='task')
router.register(r'schedule', api_views.ScheduleViewSet, basename='schedule')
router.register(r'goals', api_views.GoalViewSet, basename='goal')
router.register(r'chat/sessions', api_views.ChatSessionViewSet, basename='chat-session')
router.register(r'documents', api_views.DocumentViewSet, basename='document')
router.register(r'career/jobs', api_views.JobViewSet, basename='job')
router.register(r'notifications', api_views.NotificationViewSet, basename='notification')


# ══════════════════ API v1 URL'lar ══════════════════
v1_patterns = [
    # Auth (JWT)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('profile/', api_views.ProfileView.as_view(), name='api_profile'),

    # Daily Dashboard
    path('daily/dashboard/', api_views.DailyDashboardView.as_view(), name='api_daily_dashboard'),
    path('daily/ai-plan/', api_views.AIPlanView.as_view(), name='api_ai_plan'),

    # Career
    path('career/matches/', api_views.CareerMatchView.as_view(), name='api_career_matches'),
    path('career/skill-gap/', api_views.SkillGapView.as_view(), name='api_skill_gap'),

    # Admin
    path('admin/stats/', api_views.AdminStatsView.as_view(), name='api_admin_stats'),

    # Router URLs (tasks, schedule, goals, chat, documents, jobs, notifications)
    path('', include(router.urls)),
]

# ══════════════════ Legacy API (backward compat) ══════════════════
legacy_patterns = [
    # Chat API (eski template'lar uchun)
    path('chat/', views.chat_api, name='chat_api'),
    path('sessions/', views.get_sessions, name='get_sessions'),
    path('session/create/', views.create_session, name='create_session'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/messages/', views.get_session_messages, name='get_session_messages'),
    # Notifications
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    # OneID
    path('sync-oneid/', views.sync_oneid_api, name='sync_oneid_api'),
    # University & Docs
    path('university-search/', views.university_search, name='university_search'),
    path('upload-document/', views.upload_document, name='upload_document'),
    path('submit-test/<int:unit_id>/', views.submit_test, name='submit_test'),
    # AI Quiz
    path('generate-quiz/', views.generate_quiz_api, name='generate_quiz_api'),
    path('submit-ai-quiz/', views.submit_ai_quiz_api, name='submit_ai_quiz_api'),
    # Plan
    path('generate-plan/', views.generate_plan_api, name='generate_plan_api'),
    path('toggle-task/<int:task_id>/', views.toggle_task_api, name='toggle_task_api'),
]

# Birlashtirilgan URL'lar
urlpatterns = [
    path('v1/', include(v1_patterns)),   # Yangi DRF API: /api/v1/...
] + legacy_patterns                       # Eski API: /api/... (backward compat)
