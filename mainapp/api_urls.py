from django.urls import path
from . import views

urlpatterns = [
    # Chat API
    path('chat/', views.chat_api, name='chat_api'),
    path('sessions/', views.get_sessions, name='get_sessions'),
    path('session/create/', views.create_session, name='create_session'),
    path('session/<int:session_id>/delete/', views.delete_session, name='delete_session'),
    path('session/<int:session_id>/messages/', views.get_session_messages, name='get_session_messages'),
    # Notifications API
    path('notifications/', views.get_notifications, name='get_notifications'),
    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    # OneID Sync
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
