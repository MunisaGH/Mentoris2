from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('mentor/', views.mentor_ai, name='mentor_ai'),
    path('knowledge/', views.knowledge_base, name='knowledge_base'),
    path('career/', views.career_hub, name='career_hub'),
    path('gov/', views.gov_services, name='gov_services'),
    path('profile/complete/', views.complete_profile, name='complete_profile'),
    path('profile/', views.profile_settings, name='profile_settings'),
    # Chat API
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/sessions/', views.get_sessions, name='get_sessions'),
    path('api/session/create/', views.create_session, name='create_session'),
    path('api/session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('api/session/<int:session_id>/messages/', views.get_session_messages, name='get_session_messages'),
    # Notifications API
    path('api/notifications/', views.get_notifications, name='get_notifications'),
    path('api/notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('api/notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    # OneID Sync
    path('api/sync-oneid/', views.sync_oneid_api, name='sync_oneid_api'),
    # Stage 1: University & Docs
    path('api/university-search/', views.university_search, name='university_search'),
    path('api/upload-document/', views.upload_document, name='upload_document'),
    path('test/<int:unit_id>/', views.take_test, name='take_test'),
    path('api/submit-test/<int:unit_id>/', views.submit_test, name='submit_test'),
    path('ai-quiz/', views.ai_quiz_view, name='ai_quiz_view'),
    path('api/generate-quiz/', views.generate_quiz_api, name='generate_quiz_api'),
    path('api/submit-ai-quiz/', views.submit_ai_quiz_api, name='submit_ai_quiz_api'),
    path('api/generate-plan/', views.generate_plan_api, name='generate_plan_api'),
    path('api/toggle-task/<int:task_id>/', views.toggle_task_api, name='toggle_task_api'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
]
