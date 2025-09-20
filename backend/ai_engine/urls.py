"""
URL configuration for ai_engine app
"""
from django.urls import path
from . import views

app_name = 'ai_engine'

urlpatterns = [
    # AI Dashboard
    path('dashboard/', views.ai_dashboard, name='ai_dashboard'),
    
    # Stability Score API
    path('api/stability/', views.calculate_stability, name='calculate_stability'),
    path('api/predictions/', views.generate_predictions, name='generate_predictions'),
    
    # Medicine Alert APIs
    path('api/medicine-alerts/', views.medicine_alerts_api, name='medicine_alerts_api'),
    path('api/medicine-alerts/<int:alert_id>/', views.medicine_alert_detail_api, name='medicine_alert_detail_api'),
    
    # Medicine Intake APIs
    path('api/medicine-intake/', views.record_medicine_intake_api, name='record_medicine_intake_api'),
    path('api/medicine-intake/history/', views.medicine_intake_history_api, name='medicine_intake_history_api'),
    
    # WebLLM AI Nudge APIs
    path('api/ai-nudges/generate/', views.generate_ai_nudge_api, name='generate_ai_nudge_api'),
    path('api/ai-nudges/<int:nudge_id>/update/', views.update_ai_nudge_api, name='update_ai_nudge_api'),
    path('api/ai-nudges/', views.get_ai_nudges_api, name='get_ai_nudges_api'),
    path('api/ai-nudges/<int:nudge_id>/interaction/', views.nudge_interaction_api, name='nudge_interaction_api'),
    
    # WebLLM Session Tracking
    path('api/webllm-session/', views.webllm_session_api, name='webllm_session_api'),
]