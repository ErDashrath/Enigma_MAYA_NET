"""
URL patterns for the vitals app
"""
from django.urls import path
from . import views

app_name = 'vitals'

urlpatterns = [
    # Vital Signs
    path('record/', views.record_vitals, name='record_vitals'),
    path('trends/', views.vitals_trends, name='vitals_trends'),
    path('api/vitals/', views.vitals_api, name='vitals_api'),
    
    # Lifestyle Metrics
    path('lifestyle/', views.record_lifestyle, name='record_lifestyle'),
    path('api/lifestyle/', views.lifestyle_api, name='lifestyle_api'),
    
    # Symptom Reports
    path('symptoms/', views.report_symptoms, name='report_symptoms'),
    path('api/symptoms/', views.symptoms_api, name='symptoms_api'),
    
    # Medical History
    path('medical-history/', views.medical_history_view, name='medical_history'),
    path('api/medical-history/', views.medical_history_api, name='medical_history_api'),
    
    # Risk Assessment
    path('risk-assessment/', views.risk_assessment_view, name='risk_assessment'),
    path('api/risk-assessment/', views.risk_assessment_api, name='risk_assessment_api'),
    
    # LLaMA Risk Prediction API
    path('api/risk-predict/', views.RiskPredictView.as_view(), name='risk_predict'),
    
    # Comprehensive Vitals Logging API
    path('api/log-comprehensive/', views.log_comprehensive_vitals, name='log_comprehensive_vitals'),
]