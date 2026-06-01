from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_view, name='edu_search'),
    path('slots/', views.slots_view, name='edu_slots'),
    path('career-mentor/', views.career_mentor, name='career_mentor'),
    path('analytics/', views.dataset_analytics, name='dataset_analytics'),
    path('download-nlp/', views.download_nlp_report, name='download_nlp_report'),
    path('download-global-dataset/', views.download_global_dataset, name='download_global_dataset'),
]
