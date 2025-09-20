"""
URL configuration for core app
"""
from django.urls import path
from . import views

urlpatterns = [
    # Frontend template views
    path('', views.home_view, name='home'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('vitals/', views.vitals_view, name='vitals'),
    path('reports/', views.reports_view, name='reports'),
    
    # Authentication views
    path('auth/login/', views.login_view, name='login'),
    path('auth/register/', views.register_view, name='register'),
    path('auth/logout/', views.logout_view, name='logout'),
    path('auth/profile/', views.profile_view, name='profile'),
    
    # AJAX API endpoints
    path('api/stability-score/', views.api_stability_score, name='api_stability_score'),
]