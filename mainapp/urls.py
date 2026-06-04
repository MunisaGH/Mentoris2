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
    path('test/<int:unit_id>/', views.take_test, name='take_test'),
    path('ai-quiz/', views.ai_quiz_view, name='ai_quiz_view'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
]
