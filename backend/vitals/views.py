"""
Vitals app views - Business logic for vital signs and lifestyle metrics
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Avg, Max, Min, Count
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import VitalSigns, LifestyleMetrics, SymptomReport, MedicalHistory, RiskAssessment
from .serializers import RiskInputSerializer, RiskOutputSerializer
from patients.models import PatientProfile, PatientNote
from patients.views import PatientNoteService
from model_runner.llama_runner import run_llama


class VitalSignsService:
    """Business logic for vital signs management"""
    
    @staticmethod
    def record_vital_signs(patient_profile, vitals_data):
        """Record new vital signs with validation and analysis"""
        # Validate vital signs ranges
        alerts = VitalSignsService.validate_vital_ranges(vitals_data)
        
        # Create vital signs record
        vital_signs = VitalSigns.objects.create(
            patient=patient_profile,
            systolic_bp=vitals_data.get('systolic_bp'),
            diastolic_bp=vitals_data.get('diastolic_bp'),
            heart_rate=vitals_data.get('heart_rate'),
            temperature=vitals_data.get('temperature'),
            respiratory_rate=vitals_data.get('respiratory_rate'),
            oxygen_saturation=vitals_data.get('oxygen_saturation'),
            blood_glucose=vitals_data.get('blood_glucose'),
            weight=vitals_data.get('weight'),
            height=vitals_data.get('height'),
            measured_at=vitals_data.get('measured_at', timezone.now()),
            source=vitals_data.get('source', 'manual'),
            device_info=vitals_data.get('device_info', {}),
            notes=vitals_data.get('notes', '')
        )
        
        # Create automated note if there are alerts
        if alerts:
            PatientNoteService.create_automated_note(
                patient_profile,
                'vital_signs',
                {
                    'systolic': vitals_data.get('systolic_bp', 'N/A'),
                    'diastolic': vitals_data.get('diastolic_bp', 'N/A'),
                    'heart_rate': vitals_data.get('heart_rate', 'N/A'),
                    'temperature': vitals_data.get('temperature', 'N/A'),
                    'alerts': ', '.join(alerts)
                }
            )
        
        return vital_signs, alerts
    
    @staticmethod
    def validate_vital_ranges(vitals_data):
        """Validate vital signs and return alerts for abnormal values"""
        alerts = []
        
        # Blood pressure validation
        systolic = vitals_data.get('systolic_bp')
        diastolic = vitals_data.get('diastolic_bp')
        
        if systolic and diastolic:
            if systolic >= 180 or diastolic >= 120:
                alerts.append("CRITICAL: Hypertensive crisis - seek immediate medical attention")
            elif systolic >= 140 or diastolic >= 90:
                alerts.append("HIGH: Elevated blood pressure")
            elif systolic < 90 or diastolic < 60:
                alerts.append("LOW: Blood pressure below normal range")
        
        # Heart rate validation
        heart_rate = vitals_data.get('heart_rate')
        if heart_rate:
            if heart_rate > 120:
                alerts.append("HIGH: Elevated heart rate (tachycardia)")
            elif heart_rate < 50:
                alerts.append("LOW: Low heart rate (bradycardia)")
        
        # Temperature validation
        temperature = vitals_data.get('temperature')
        if temperature:
            if temperature >= 103:
                alerts.append("CRITICAL: High fever - seek medical attention")
            elif temperature >= 100.4:
                alerts.append("FEVER: Elevated temperature")
            elif temperature < 95:
                alerts.append("LOW: Below normal body temperature")
        
        # Oxygen saturation validation
        oxygen_sat = vitals_data.get('oxygen_saturation')
        if oxygen_sat:
            if oxygen_sat < 90:
                alerts.append("CRITICAL: Low oxygen saturation - seek immediate care")
            elif oxygen_sat < 95:
                alerts.append("LOW: Oxygen saturation below normal")
        
        # Blood glucose validation
        blood_glucose = vitals_data.get('blood_glucose')
        if blood_glucose:
            if blood_glucose > 250:
                alerts.append("HIGH: Severely elevated blood sugar")
            elif blood_glucose > 180:
                alerts.append("HIGH: Elevated blood sugar")
            elif blood_glucose < 70:
                alerts.append("LOW: Low blood sugar (hypoglycemia)")
        
        return alerts
    
    @staticmethod
    def get_vitals_trends(patient_profile, days=30):
        """Get trend analysis for vital signs over specified period"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        vitals = VitalSigns.objects.filter(
            patient=patient_profile,
            recorded_at__gte=start_date
        ).order_by('recorded_at')
        
        if not vitals.exists():
            return None
        
        # Calculate averages and trends
        trends = {
            'period_days': days,
            'total_readings': vitals.count(),
            'averages': {},
            'ranges': {},
            'trends': {}
        }
        
        # Calculate averages
        avg_data = vitals.aggregate(
            avg_systolic=Avg('systolic_bp'),
            avg_diastolic=Avg('diastolic_bp'),
            avg_heart_rate=Avg('heart_rate'),
            avg_temperature=Avg('temperature'),
            avg_weight=Avg('weight')
        )
        
        trends['averages'] = {k: round(v, 1) if v else None for k, v in avg_data.items()}
        
        # Calculate ranges
        range_data = vitals.aggregate(
            max_systolic=Max('systolic_bp'),
            min_systolic=Min('systolic_bp'),
            max_heart_rate=Max('heart_rate'),
            min_heart_rate=Min('heart_rate')
        )
        
        trends['ranges'] = range_data
        
        # Calculate trend direction (simple comparison of first vs last week)
        if vitals.count() >= 7:
            first_week = vitals[:7]
            last_week = vitals[max(0, vitals.count()-7):]
            
            first_avg_bp = first_week.aggregate(Avg('systolic_bp'))['systolic_bp__avg'] or 0
            last_avg_bp = last_week.aggregate(Avg('systolic_bp'))['systolic_bp__avg'] or 0
            
            if last_avg_bp > first_avg_bp + 5:
                trends['trends']['blood_pressure'] = 'increasing'
            elif last_avg_bp < first_avg_bp - 5:
                trends['trends']['blood_pressure'] = 'decreasing'
            else:
                trends['trends']['blood_pressure'] = 'stable'
        
        return trends
    
    @staticmethod
    def get_bp_category(systolic, diastolic):
        """Categorize blood pressure reading"""
        if not systolic or not diastolic:
            return 'unknown'
        
        if systolic < 120 and diastolic < 80:
            return 'normal'
        elif systolic < 130 and diastolic < 80:
            return 'elevated'
        elif systolic < 140 or diastolic < 90:
            return 'stage1_hypertension'
        elif systolic < 180 or diastolic < 120:
            return 'stage2_hypertension'
        else:
            return 'hypertensive_crisis'


class LifestyleMetricsService:
    """Business logic for lifestyle metrics"""
    
    @staticmethod
    def record_lifestyle_metrics(patient_profile, metrics_data):
        """Record lifestyle metrics with analysis"""
        lifestyle_metrics = LifestyleMetrics.objects.create(
            patient=patient_profile,
            stress_level=metrics_data.get('stress_level'),
            sleep_hours=metrics_data.get('sleep_hours'),
            sleep_quality=metrics_data.get('sleep_quality'),
            exercise_minutes=metrics_data.get('exercise_minutes'),
            exercise_intensity=metrics_data.get('exercise_intensity'),
            diet_quality=metrics_data.get('diet_quality'),
            water_intake=metrics_data.get('water_intake'),
            medication_adherence=metrics_data.get('medication_adherence'),
            mood_rating=metrics_data.get('mood_rating'),
            notes=metrics_data.get('notes', '')
        )
        
        # Generate insights
        insights = LifestyleMetricsService.generate_lifestyle_insights(lifestyle_metrics)
        
        return lifestyle_metrics, insights
    
    @staticmethod
    def generate_lifestyle_insights(lifestyle_metrics):
        """Generate insights based on lifestyle metrics"""
        insights = []
        
        # Sleep analysis
        if lifestyle_metrics.sleep_hours:
            if lifestyle_metrics.sleep_hours < 6:
                insights.append("Consider increasing sleep duration for better health")
            elif lifestyle_metrics.sleep_hours > 9:
                insights.append("Monitor for potential sleep disorders")
        
        if lifestyle_metrics.sleep_quality and lifestyle_metrics.sleep_quality <= 2:
            insights.append("Poor sleep quality may affect overall health")
        
        # Exercise analysis
        if lifestyle_metrics.exercise_minutes:
            weekly_target = 150  # minutes per week
            if lifestyle_metrics.exercise_minutes * 7 < weekly_target:
                insights.append("Consider increasing physical activity")
        
        # Stress analysis
        if lifestyle_metrics.stress_level and lifestyle_metrics.stress_level >= 4:
            insights.append("High stress levels - consider stress management techniques")
        
        # Medication adherence
        if lifestyle_metrics.medication_adherence and lifestyle_metrics.medication_adherence < 80:
            insights.append("Medication adherence below recommended level")
        
        return insights
    
    @staticmethod
    def get_lifestyle_summary(patient_profile, days=7):
        """Get lifestyle metrics summary for specified period"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        metrics = LifestyleMetrics.objects.filter(
            patient=patient_profile,
            recorded_at__gte=start_date
        )
        
        if not metrics.exists():
            return None
        
        summary = metrics.aggregate(
            avg_stress=Avg('stress_level'),
            avg_sleep_hours=Avg('sleep_hours'),
            avg_sleep_quality=Avg('sleep_quality'),
            avg_exercise=Avg('exercise_minutes'),
            avg_diet_quality=Avg('diet_quality'),
            avg_medication_adherence=Avg('medication_adherence'),
            avg_mood=Avg('mood_rating')
        )
        
        # Round values
        for key, value in summary.items():
            if value:
                summary[key] = round(value, 1)
        
        return summary


class SymptomReportService:
    """Business logic for symptom reporting"""
    
    @staticmethod
    def report_symptoms(patient_profile, symptoms_data):
        """Record symptom report with severity assessment"""
        symptom_report = SymptomReport.objects.create(
            patient=patient_profile,
            symptoms=symptoms_data.get('symptoms', []),
            severity_level=symptoms_data.get('severity_level'),
            duration_hours=symptoms_data.get('duration_hours'),
            triggers=symptoms_data.get('triggers', []),
            relief_methods=symptoms_data.get('relief_methods', []),
            additional_notes=symptoms_data.get('additional_notes', '')
        )
        
        # Check for urgent symptoms
        urgent_alerts = SymptomReportService.check_urgent_symptoms(symptom_report)
        
        # Create automated note
        PatientNoteService.create_automated_note(
            patient_profile,
            'symptom',
            {
                'symptoms': ', '.join(symptom_report.symptoms),
                'severity': symptom_report.get_severity_level_display(),
                'duration': f"{symptom_report.duration_hours} hours" if symptom_report.duration_hours else "Unknown"
            }
        )
        
        return symptom_report, urgent_alerts
    
    @staticmethod
    def check_urgent_symptoms(symptom_report):
        """Check for symptoms requiring immediate attention"""
        urgent_symptoms = [
            'chest pain', 'difficulty breathing', 'severe headache',
            'confusion', 'loss of consciousness', 'severe bleeding',
            'severe abdominal pain', 'signs of stroke'
        ]
        
        alerts = []
        
        # Check for urgent symptoms
        for symptom in symptom_report.symptoms:
            if any(urgent in symptom.lower() for urgent in urgent_symptoms):
                alerts.append(f"URGENT: {symptom} requires immediate medical attention")
        
        # Check severity level
        if symptom_report.severity_level >= 4:
            alerts.append("High severity symptoms - consider medical evaluation")
        
        return alerts


# Django views
@login_required
def vitals_dashboard(request):
    """Vitals dashboard view"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        # Get recent vitals
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at')[:10]
        
        # Get trends
        trends = VitalSignsService.get_vitals_trends(patient_profile)
        
        # Get lifestyle summary
        lifestyle_summary = LifestyleMetricsService.get_lifestyle_summary(patient_profile)
        
        return render(request, 'vitals/dashboard.html', {
            'recent_vitals': recent_vitals,
            'trends': trends,
            'lifestyle_summary': lifestyle_summary
        })
        
    except PatientProfile.DoesNotExist:
        return render(request, 'patients/create_profile.html')


@login_required
def record_vitals(request):
    """Record new vital signs"""
    if request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            
            vitals_data = {
                'systolic_bp': request.POST.get('systolic_bp'),
                'diastolic_bp': request.POST.get('diastolic_bp'),
                'heart_rate': request.POST.get('heart_rate'),
                'temperature': request.POST.get('temperature'),
                'respiratory_rate': request.POST.get('respiratory_rate'),
                'oxygen_saturation': request.POST.get('oxygen_saturation'),
                'blood_glucose': request.POST.get('blood_glucose'),
                'weight': request.POST.get('weight'),
                'notes': request.POST.get('notes', '')
            }
            
            # Convert string values to float where applicable
            for key, value in vitals_data.items():
                if key != 'notes' and value:
                    try:
                        vitals_data[key] = float(value)
                    except ValueError:
                        vitals_data[key] = None
            
            vital_signs, alerts = VitalSignsService.record_vital_signs(patient_profile, vitals_data)
            
            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'vital_id': vital_signs.id
            })
            
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return render(request, 'vitals/record_vitals.html')


@login_required
def report_symptoms(request):
    """Symptom reporting view"""
    if request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            
            symptoms_data = {
                'symptoms': request.POST.getlist('symptoms'),
                'severity_level': int(request.POST.get('severity_level', 1)),
                'duration_hours': float(request.POST.get('duration_hours', 0)) if request.POST.get('duration_hours') else None,
                'triggers': request.POST.getlist('triggers'),
                'relief_methods': request.POST.getlist('relief_methods'),
                'additional_notes': request.POST.get('additional_notes', '')
            }
            
            symptom_report, alerts = SymptomReportService.report_symptoms(patient_profile, symptoms_data)
            
            return JsonResponse({
                'success': True,
                'alerts': alerts,
                'report_id': symptom_report.id
            })
            
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # Get recent symptom reports for display
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        recent_reports = SymptomReport.objects.filter(
            patient=patient_profile
        ).order_by('-reported_at')[:5]
        
        return render(request, 'vitals/report_symptoms.html', {
            'recent_reports': recent_reports
        })
        
    except PatientProfile.DoesNotExist:
        return render(request, 'patients/create_profile.html')


class MedicalHistoryService:
    """Business logic for medical history management"""
    
    @staticmethod
    def update_medical_history(patient_profile, history_data):
        """Update or create medical history record"""
        from .models import MedicalHistory
        
        history, created = MedicalHistory.objects.get_or_create(
            patient=patient_profile,
            defaults={
                'chronic_conditions': history_data.get('chronic_conditions', []),
                'past_episodes': history_data.get('past_episodes', []),
                'family_history': history_data.get('family_history', {}),
                'risk_factors': history_data.get('risk_factors', []),
                'allergies': history_data.get('allergies', []),
                'current_medications': history_data.get('current_medications', []),
                'notes': history_data.get('notes', '')
            }
        )
        
        if not created:
            # Update existing record
            for field, value in history_data.items():
                if hasattr(history, field):
                    setattr(history, field, value)
            history.save()
        
        return history
    
    @staticmethod
    def add_medical_episode(patient_profile, episode_type, description="", severity=None):
        """Add a new medical episode to patient's history"""
        from .models import MedicalHistory
        
        try:
            history = MedicalHistory.objects.get(patient=patient_profile)
        except MedicalHistory.DoesNotExist:
            history = MedicalHistory.objects.create(patient=patient_profile)
        
        history.add_episode(episode_type, timezone.now(), description, severity)
        return history


class RiskAssessmentService:
    """Business logic for risk assessment calculations"""
    
    @staticmethod
    def calculate_risk_score(patient_profile):
        """Calculate comprehensive risk assessment for patient"""
        from .models import MedicalHistory, RiskAssessment
        
        # Get recent data for calculation
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile,
            measured_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-measured_at')
        
        recent_lifestyle = LifestyleMetrics.objects.filter(
            patient=patient_profile,
            recorded_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-recorded_at')
        
        try:
            medical_history = MedicalHistory.objects.get(patient=patient_profile)
        except MedicalHistory.DoesNotExist:
            medical_history = None
        
        # Calculate component scores
        vital_signs_score = RiskAssessmentService._calculate_vitals_score(recent_vitals)
        lifestyle_score = RiskAssessmentService._calculate_lifestyle_score(recent_lifestyle)
        medication_adherence_score = RiskAssessmentService._calculate_adherence_score(recent_lifestyle)
        
        # Calculate overall stability score
        stability_score = (vital_signs_score * 0.4 + 
                          lifestyle_score * 0.3 + 
                          medication_adherence_score * 0.3)
        
        # Determine risk level
        if stability_score >= 80:
            risk_level = 'low'
        elif stability_score >= 60:
            risk_level = 'moderate'
        elif stability_score >= 40:
            risk_level = 'high'
        else:
            risk_level = 'critical'
        
        # Calculate adverse event probability
        adverse_event_probability = max(0, min(1, (100 - stability_score) / 100))
        adverse_event_risk = adverse_event_probability > 0.5
        
        # Identify risk factors
        risk_factors = RiskAssessmentService._identify_risk_factors(
            recent_vitals, recent_lifestyle, medical_history
        )
        
        # Generate recommendations
        recommendations = RiskAssessmentService._generate_recommendations(
            risk_factors, stability_score
        )
        
        # Create risk assessment record
        risk_assessment = RiskAssessment.objects.create(
            patient=patient_profile,
            stability_score=stability_score,
            risk_level=risk_level,
            adverse_event_risk=adverse_event_risk,
            adverse_event_probability=adverse_event_probability,
            vital_signs_score=vital_signs_score,
            lifestyle_score=lifestyle_score,
            medication_adherence_score=medication_adherence_score,
            risk_factors=risk_factors,
            recommendations=recommendations,
            data_points_used={
                'vitals_count': recent_vitals.count(),
                'lifestyle_count': recent_lifestyle.count(),
                'has_medical_history': medical_history is not None
            },
            expires_at=timezone.now() + timedelta(hours=48)
        )
        
        return risk_assessment
    
    @staticmethod
    def _calculate_vitals_score(vitals_queryset):
        """Calculate vitals component score"""
        if not vitals_queryset.exists():
            return 50.0  # Default neutral score
        
        latest_vitals = vitals_queryset.first()
        score = 100.0
        
        # Blood pressure scoring
        if latest_vitals.systolic_bp and latest_vitals.diastolic_bp:
            if latest_vitals.systolic_bp >= 180 or latest_vitals.diastolic_bp >= 120:
                score -= 30
            elif latest_vitals.systolic_bp >= 140 or latest_vitals.diastolic_bp >= 90:
                score -= 15
        
        # Heart rate scoring
        if latest_vitals.heart_rate:
            if latest_vitals.heart_rate > 120 or latest_vitals.heart_rate < 50:
                score -= 15
        
        # Blood glucose scoring
        if latest_vitals.blood_glucose:
            if latest_vitals.blood_glucose > 250 or latest_vitals.blood_glucose < 70:
                score -= 20
            elif latest_vitals.blood_glucose > 180:
                score -= 10
        
        # Oxygen saturation scoring
        if latest_vitals.oxygen_saturation:
            if latest_vitals.oxygen_saturation < 90:
                score -= 25
            elif latest_vitals.oxygen_saturation < 95:
                score -= 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def _calculate_lifestyle_score(lifestyle_queryset):
        """Calculate lifestyle component score"""
        if not lifestyle_queryset.exists():
            return 50.0  # Default neutral score
        
        latest_lifestyle = lifestyle_queryset.first()
        score = 100.0
        
        # Stress level scoring
        if latest_lifestyle.stress_level:
            if latest_lifestyle.stress_level >= 4:
                score -= 15
            elif latest_lifestyle.stress_level >= 3:
                score -= 5
        
        # Sleep scoring
        if latest_lifestyle.sleep_hours:
            if latest_lifestyle.sleep_hours < 6 or latest_lifestyle.sleep_hours > 9:
                score -= 10
        
        # Activity scoring
        if latest_lifestyle.activity_level:
            if latest_lifestyle.activity_level <= 2:
                score -= 10
        
        return max(0, min(100, score))
    
    @staticmethod
    def _calculate_adherence_score(lifestyle_queryset):
        """Calculate medication adherence score"""
        if not lifestyle_queryset.exists():
            return 50.0  # Default neutral score
        
        recent_entries = lifestyle_queryset[:7]  # Last 7 days
        adherence_scores = []
        
        for entry in recent_entries:
            if entry.medication_adherence_percentage is not None:
                adherence_scores.append(entry.medication_adherence_percentage)
            elif entry.medication_taken is not None:
                adherence_scores.append(100.0 if entry.medication_taken else 0.0)
        
        if adherence_scores:
            return sum(adherence_scores) / len(adherence_scores)
        return 50.0
    
    @staticmethod
    def _identify_risk_factors(vitals_queryset, lifestyle_queryset, medical_history):
        """Identify current risk factors"""
        risk_factors = []
        
        # Check vitals-based risk factors
        if vitals_queryset.exists():
            latest_vitals = vitals_queryset.first()
            if latest_vitals.systolic_bp and latest_vitals.systolic_bp >= 140:
                risk_factors.append("Elevated blood pressure")
            if latest_vitals.blood_glucose and latest_vitals.blood_glucose > 180:
                risk_factors.append("Elevated blood glucose")
            if latest_vitals.bmi and latest_vitals.bmi >= 30:
                risk_factors.append("Obesity")
        
        # Check lifestyle-based risk factors
        if lifestyle_queryset.exists():
            latest_lifestyle = lifestyle_queryset.first()
            if latest_lifestyle.stress_level and latest_lifestyle.stress_level >= 4:
                risk_factors.append("High stress level")
            if latest_lifestyle.sleep_hours and latest_lifestyle.sleep_hours < 6:
                risk_factors.append("Insufficient sleep")
            if latest_lifestyle.activity_level and latest_lifestyle.activity_level <= 2:
                risk_factors.append("Sedentary lifestyle")
        
        # Check medical history risk factors
        if medical_history:
            if medical_history.has_diabetes():
                risk_factors.append("Diabetes")
            if 'hypertension' in medical_history.chronic_conditions:
                risk_factors.append("Hypertension")
        
        return risk_factors
    
    @staticmethod
    def _generate_recommendations(risk_factors, stability_score):
        """Generate personalized recommendations"""
        recommendations = []
        
        if "Elevated blood pressure" in risk_factors:
            recommendations.append("Monitor blood pressure daily and consult your doctor")
        if "Elevated blood glucose" in risk_factors:
            recommendations.append("Check blood glucose more frequently and review diet")
        if "High stress level" in risk_factors:
            recommendations.append("Practice stress reduction techniques like meditation")
        if "Insufficient sleep" in risk_factors:
            recommendations.append("Aim for 7-8 hours of sleep per night")
        if "Sedentary lifestyle" in risk_factors:
            recommendations.append("Increase daily physical activity gradually")
        
        if stability_score < 50:
            recommendations.append("Consider scheduling an appointment with your healthcare provider")
        
        return recommendations


@login_required
def medical_history_view(request):
    """Medical history management view"""
    from .models import MedicalHistory
    
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        if request.method == 'POST':
            history_data = {
                'chronic_conditions': request.POST.getlist('chronic_conditions'),
                'risk_factors': request.POST.getlist('risk_factors'),
                'allergies': request.POST.getlist('allergies'),
                'current_medications': request.POST.getlist('current_medications'),
                'notes': request.POST.get('notes', '')
            }
            
            history = MedicalHistoryService.update_medical_history(patient_profile, history_data)
            
            return JsonResponse({
                'success': True,
                'message': 'Medical history updated successfully'
            })
        
        # Get existing medical history
        try:
            history = MedicalHistory.objects.get(patient=patient_profile)
        except MedicalHistory.DoesNotExist:
            history = None
        
        return render(request, 'vitals/medical_history.html', {
            'medical_history': history
        })
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})


@login_required
def risk_assessment_view(request):
    """Risk assessment view"""
    from .models import RiskAssessment
    
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        # Calculate new risk assessment
        risk_assessment = RiskAssessmentService.calculate_risk_score(patient_profile)
        
        # Get recent assessments for trend analysis
        recent_assessments = RiskAssessment.objects.filter(
            patient=patient_profile
        ).order_by('-calculated_at')[:10]
        
        return render(request, 'vitals/risk_assessment.html', {
            'current_assessment': risk_assessment,
            'recent_assessments': recent_assessments
        })
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})


@login_required
def log_comprehensive_vitals(request):
    """
    Comprehensive vitals logging API endpoint that handles all types of health data:
    - Vital Signs (blood pressure, heart rate, glucose, weight, BMI, oxygen saturation)
    - Lifestyle Metrics (steps, activity level, sleep, diet, stress, medication adherence)
    - Medical History updates
    - Automatic risk assessment calculation
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST method required'})
    
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        data = json.loads(request.body)
        
        response_data = {
            'success': True,
            'logged': [],
            'alerts': [],
            'risk_assessment': None
        }
        
        # 1. Log Vital Signs if provided
        if 'vitals' in data:
            vitals_data = data['vitals']
            # Add timestamp if not provided
            if 'measured_at' not in vitals_data:
                vitals_data['measured_at'] = timezone.now()
            
            vital_signs, alerts = VitalSignsService.record_vital_signs(patient_profile, vitals_data)
            response_data['logged'].append({
                'type': 'vital_signs',
                'id': vital_signs.id,
                'blood_pressure': vital_signs.blood_pressure_reading,
                'bmi': vital_signs.bmi,
                'glucose_category': vital_signs.glucose_category
            })
            response_data['alerts'].extend(alerts)
        
        # 2. Log Lifestyle Metrics if provided
        if 'lifestyle' in data:
            lifestyle_data = data['lifestyle']
            # Add timestamp if not provided
            if 'recorded_at' not in lifestyle_data:
                lifestyle_data['recorded_at'] = timezone.now()
            
            lifestyle_metrics = LifestyleMetrics.objects.create(
                patient=patient_profile,
                stress_level=lifestyle_data.get('stress_level'),
                mood_rating=lifestyle_data.get('mood_rating'),
                sleep_hours=lifestyle_data.get('sleep_hours'),
                sleep_quality=lifestyle_data.get('sleep_quality'),
                sodium_intake=lifestyle_data.get('sodium_intake'),
                water_intake=lifestyle_data.get('water_intake'),
                calorie_intake=lifestyle_data.get('calorie_intake'),
                food_log=lifestyle_data.get('food_log', {}),
                activity_level=lifestyle_data.get('activity_level'),
                exercise_minutes=lifestyle_data.get('exercise_minutes'),
                steps_count=lifestyle_data.get('steps_count'),
                medication_taken=lifestyle_data.get('medication_taken'),
                missed_doses=lifestyle_data.get('missed_doses', 0),
                medication_adherence_percentage=lifestyle_data.get('medication_adherence_percentage'),
                recorded_at=lifestyle_data['recorded_at'],
                notes=lifestyle_data.get('notes', '')
            )
            
            response_data['logged'].append({
                'type': 'lifestyle_metrics',
                'id': lifestyle_metrics.id,
                'activity_level': lifestyle_metrics.activity_level_display,
                'stress_level': lifestyle_metrics.stress_level_display
            })
        
        # 3. Update Medical History if provided
        if 'medical_history' in data:
            history_data = data['medical_history']
            history = MedicalHistoryService.update_medical_history(patient_profile, history_data)
            response_data['logged'].append({
                'type': 'medical_history',
                'id': history.id,
                'conditions_count': len(history.chronic_conditions),
                'medications_count': len(history.current_medications)
            })
        
        # 4. Add Medical Episode if provided
        if 'medical_episode' in data:
            episode_data = data['medical_episode']
            history = MedicalHistoryService.add_medical_episode(
                patient_profile,
                episode_data.get('type'),
                episode_data.get('description', ''),
                episode_data.get('severity')
            )
            response_data['logged'].append({
                'type': 'medical_episode',
                'episode_type': episode_data.get('type'),
                'description': episode_data.get('description', '')
            })
        
        # 5. Calculate Risk Assessment if vitals or lifestyle data was logged
        if 'vitals' in data or 'lifestyle' in data:
            try:
                risk_assessment = RiskAssessmentService.calculate_risk_score(patient_profile)
                response_data['risk_assessment'] = {
                    'id': risk_assessment.id,
                    'stability_score': risk_assessment.stability_score,
                    'risk_level': risk_assessment.risk_level,
                    'adverse_event_probability': risk_assessment.risk_percentage,
                    'risk_factors': risk_assessment.risk_factors,
                    'recommendations': risk_assessment.recommendations
                }
                
                # Add high-risk alert if needed
                if risk_assessment.is_high_risk:
                    response_data['alerts'].append(
                        f"HIGH RISK: {risk_assessment.risk_level.title()} risk level detected. "
                        f"Consider consulting your healthcare provider."
                    )
                    
            except Exception as e:
                response_data['risk_assessment_error'] = str(e)
        
        return JsonResponse(response_data)
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def vitals_api(request):
    """API endpoint for vitals data"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        if request.method == 'GET':
            # Get recent vitals
            days = int(request.GET.get('days', 30))
            vitals = VitalSigns.objects.filter(
                patient=patient_profile,
                measured_at__gte=timezone.now() - timedelta(days=days)
            ).order_by('-measured_at')
            
            vitals_data = []
            for vital in vitals:
                vitals_data.append({
                    'id': vital.id,
                    'measured_at': vital.measured_at.isoformat(),
                    'systolic_bp': vital.systolic_bp,
                    'diastolic_bp': vital.diastolic_bp,
                    'blood_pressure': vital.blood_pressure_reading,
                    'bp_category': vital.bp_category,
                    'heart_rate': vital.heart_rate,
                    'temperature': vital.temperature,
                    'weight': vital.weight,
                    'height': vital.height,
                    'bmi': vital.bmi,
                    'bmi_category': vital.bmi_category,
                    'blood_glucose': vital.blood_glucose,
                    'glucose_category': vital.glucose_category,
                    'oxygen_saturation': vital.oxygen_saturation,
                    'respiratory_rate': vital.respiratory_rate,
                    'source': vital.source,
                    'notes': vital.notes
                })
            
            return JsonResponse({
                'success': True,
                'vitals': vitals_data,
                'count': len(vitals_data)
            })
            
        elif request.method == 'POST':
            # Create new vital signs record
            data = json.loads(request.body)
            vital_signs, alerts = VitalSignsService.record_vital_signs(patient_profile, data)
            
            return JsonResponse({
                'success': True,
                'vital_signs': {
                    'id': vital_signs.id,
                    'blood_pressure': vital_signs.blood_pressure_reading,
                    'bmi': vital_signs.bmi,
                    'glucose_category': vital_signs.glucose_category
                },
                'alerts': alerts
            })
            
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def lifestyle_api(request):
    """API endpoint for lifestyle metrics"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        if request.method == 'GET':
            # Get recent lifestyle data
            days = int(request.GET.get('days', 30))
            lifestyle_data = LifestyleMetrics.objects.filter(
                patient=patient_profile,
                recorded_at__gte=timezone.now() - timedelta(days=days)
            ).order_by('-recorded_at')
            
            lifestyle_list = []
            for lifestyle in lifestyle_data:
                lifestyle_list.append({
                    'id': lifestyle.id,
                    'recorded_at': lifestyle.recorded_at.isoformat(),
                    'stress_level': lifestyle.stress_level,
                    'stress_level_display': lifestyle.stress_level_display,
                    'mood_rating': lifestyle.mood_rating,
                    'sleep_hours': lifestyle.sleep_hours,
                    'sleep_quality': lifestyle.sleep_quality,
                    'activity_level': lifestyle.activity_level,
                    'activity_level_display': lifestyle.activity_level_display,
                    'exercise_minutes': lifestyle.exercise_minutes,
                    'steps_count': lifestyle.steps_count,
                    'sodium_intake': lifestyle.sodium_intake,
                    'water_intake': lifestyle.water_intake,
                    'calorie_intake': lifestyle.calorie_intake,
                    'food_log': lifestyle.food_log,
                    'total_food_servings': lifestyle.total_food_servings,
                    'medication_taken': lifestyle.medication_taken,
                    'medication_adherence_percentage': lifestyle.medication_adherence_percentage,
                    'notes': lifestyle.notes
                })
            
            return JsonResponse({
                'success': True,
                'lifestyle_metrics': lifestyle_list,
                'count': len(lifestyle_list)
            })
            
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def risk_assessment_api(request):
    """API endpoint for risk assessments"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        if request.method == 'GET':
            # Get recent risk assessments
            assessments = RiskAssessment.objects.filter(
                patient=patient_profile
            ).order_by('-calculated_at')[:10]
            
            assessment_data = []
            for assessment in assessments:
                assessment_data.append({
                    'id': assessment.id,
                    'calculated_at': assessment.calculated_at.isoformat(),
                    'stability_score': assessment.stability_score,
                    'risk_level': assessment.risk_level,
                    'adverse_event_risk': assessment.adverse_event_risk,
                    'adverse_event_probability': assessment.risk_percentage,
                    'vital_signs_score': assessment.vital_signs_score,
                    'lifestyle_score': assessment.lifestyle_score,
                    'medication_adherence_score': assessment.medication_adherence_score,
                    'risk_factors': assessment.risk_factors,
                    'recommendations': assessment.recommendations,
                    'confidence_level': assessment.confidence_level,
                    'expires_at': assessment.expires_at.isoformat()
                })
            
            return JsonResponse({
                'success': True,
                'risk_assessments': assessment_data,
                'count': len(assessment_data)
            })
            
        elif request.method == 'POST':
            # Calculate new risk assessment
            risk_assessment = RiskAssessmentService.calculate_risk_score(patient_profile)
            
            return JsonResponse({
                'success': True,
                'risk_assessment': {
                    'id': risk_assessment.id,
                    'stability_score': risk_assessment.stability_score,
                    'risk_level': risk_assessment.risk_level,
                    'adverse_event_probability': risk_assessment.risk_percentage,
                    'risk_factors': risk_assessment.risk_factors,
                    'recommendations': risk_assessment.recommendations
                }
            })
            
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


# Missing View Functions for URL Patterns
@login_required
def vitals_trends(request):
    """Display vitals trends and analytics"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        trends_data = VitalSignsService.get_vitals_trends(patient_profile, days=30)
        
        context = {
            'trends_data': trends_data,
            'patient': patient_profile
        }
        return render(request, 'vitals/trends.html', context)
    except PatientProfile.DoesNotExist:
        return render(request, 'error.html', {'message': 'Patient profile not found'})


@api_view(['GET', 'POST'])
def vitals_api(request):
    """API endpoint for vitals data"""
    if request.method == 'GET':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            vitals = VitalSigns.objects.filter(patient=patient_profile).order_by('-measured_at')[:10]
            
            vitals_data = []
            for vital in vitals:
                # Calculate BMI if height and weight available
                bmi = None
                if vital.height and vital.weight:
                    height_m = vital.height * 0.0254
                    weight_kg = vital.weight * 0.453592
                    bmi = round(weight_kg / (height_m * height_m), 2)
                
                vitals_data.append({
                    'id': vital.id,
                    'systolic': vital.systolic_bp,
                    'diastolic': vital.diastolic_bp,
                    'heart_rate': vital.heart_rate,
                    'temperature': vital.temperature,
                    'weight': vital.weight,
                    'height': vital.height,
                    'blood_glucose': vital.blood_glucose,
                    'oxygen_saturation': vital.oxygen_saturation,
                    'bmi': bmi,
                    'measured_at': vital.measured_at.isoformat(),
                    'recorded_at': vital.created_at.isoformat()
                })
            
            return JsonResponse({'success': True, 'vitals': vitals_data})
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    
    elif request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            vitals_data = json.loads(request.body)
            
            # Create comprehensive vitals record
            vital_signs = VitalSigns.objects.create(
                patient=patient_profile,
                systolic_bp=vitals_data.get('systolic'),
                diastolic_bp=vitals_data.get('diastolic'),
                heart_rate=vitals_data.get('heart_rate'),
                temperature=vitals_data.get('temperature'),
                weight=vitals_data.get('weight'),
                height=vitals_data.get('height'),
                blood_glucose=vitals_data.get('blood_glucose'),
                oxygen_saturation=vitals_data.get('oxygen_saturation'),
                measured_at=timezone.now(),
                source='manual'
            )
            
            # Calculate BMI if height and weight provided
            bmi_value = None
            if vital_signs.height and vital_signs.weight:
                height_m = vital_signs.height * 0.0254
                weight_kg = vital_signs.weight * 0.453592
                bmi_value = weight_kg / (height_m * height_m)
            
            response_data = {
                'success': True,
                'vital_id': vital_signs.id,
                'message': 'Vitals recorded successfully',
                'bmi': round(bmi_value, 2) if bmi_value else None,
                'recorded_at': vital_signs.measured_at.isoformat()
            }
            
            # If diabetes-related data provided, trigger risk assessment
            if vitals_data.get('blood_glucose') and bmi_value:
                try:
                    # Prepare diabetes assessment data
                    diabetes_input = {
                        'pregnancies': vitals_data.get('pregnancies', 0),
                        'glucose': vitals_data.get('blood_glucose'),
                        'blood_pressure': vitals_data.get('systolic', 120),
                        'skin_thickness': vitals_data.get('skin_thickness', 20),
                        'insulin': vitals_data.get('insulin', 80),
                        'bmi': bmi_value,
                        'diabetes_pedigree_function': vitals_data.get('diabetes_pedigree_function', 0.3),
                        'age': vitals_data.get('age', 30)
                    }
                    
                    # Run diabetes risk prediction
                    from hack_diabetes import get_diabetes_model
                    diabetes_model = get_diabetes_model()
                    diabetes_result = diabetes_model.predict_diabetes_risk(diabetes_input)
                    
                    response_data['diabetes_assessment'] = diabetes_result
                    
                    # Create risk assessment record
                    risk_assessment = RiskAssessment.objects.create(
                        patient=patient_profile,
                        stability_score=diabetes_result['stability_score'] * 100,
                        risk_level=diabetes_result['risk_level'],
                        risk_percentage=diabetes_result['stability_score'] * 100,
                        risk_factors=[f"Diabetes risk: {diabetes_result['diagnosis_label']}"],
                        recommendations=[f"Risk level: {diabetes_result['risk_level']}"],
                        assessment_type='diabetes_svm'
                    )
                    
                    response_data['risk_assessment_id'] = risk_assessment.id
                    
                except Exception as diabetes_error:
                    print(f"Diabetes assessment failed: {diabetes_error}")
                    response_data['diabetes_warning'] = "Diabetes assessment unavailable"
            
            return JsonResponse(response_data)
            
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@login_required
def record_lifestyle(request):
    """Record lifestyle metrics"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        if request.method == 'POST':
            lifestyle_data = {
                'daily_steps': request.POST.get('daily_steps'),
                'sleep_hours': request.POST.get('sleep_hours'),
                'stress_level': request.POST.get('stress_level'),
                'diet_category': request.POST.get('diet_category'),
                'calories': request.POST.get('calories')
            }
            
            lifestyle_metrics = LifestyleMetricsService.record_lifestyle_metrics(patient_profile, lifestyle_data)
            return JsonResponse({'success': True, 'metrics_id': lifestyle_metrics.id})
        
        return render(request, 'vitals/record_lifestyle.html', {'patient': patient_profile})
    except PatientProfile.DoesNotExist:
        return render(request, 'error.html', {'message': 'Patient profile not found'})


@api_view(['GET', 'POST'])
def lifestyle_api(request):
    """API endpoint for lifestyle metrics"""
    if request.method == 'GET':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            metrics = LifestyleMetrics.objects.filter(patient=patient_profile).order_by('-recorded_at')[:10]
            
            metrics_data = []
            for metric in metrics:
                metrics_data.append({
                    'id': metric.id,
                    'daily_steps': metric.daily_steps,
                    'sleep_hours': metric.sleep_hours,
                    'stress_level': metric.stress_level,
                    'recorded_at': metric.recorded_at.isoformat()
                })
            
            return JsonResponse({'success': True, 'metrics': metrics_data})
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    
    elif request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            lifestyle_data = json.loads(request.body)
            lifestyle_metrics = LifestyleMetricsService.record_lifestyle_metrics(patient_profile, lifestyle_data)
            
            return JsonResponse({
                'success': True,
                'metrics_id': lifestyle_metrics.id,
                'message': 'Lifestyle metrics recorded successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@api_view(['GET', 'POST'])
def symptoms_api(request):
    """API endpoint for symptom reports"""
    if request.method == 'GET':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            symptoms = SymptomReport.objects.filter(patient=patient_profile).order_by('-reported_at')[:10]
            
            symptoms_data = []
            for symptom in symptoms:
                symptoms_data.append({
                    'id': symptom.id,
                    'symptoms': symptom.symptoms,
                    'severity': symptom.severity,
                    'reported_at': symptom.reported_at.isoformat()
                })
            
            return JsonResponse({'success': True, 'symptoms': symptoms_data})
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    
    elif request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            symptoms_data = json.loads(request.body)
            symptom_report = SymptomReportService.report_symptoms(patient_profile, symptoms_data)
            
            return JsonResponse({
                'success': True,
                'report_id': symptom_report.id,
                'message': 'Symptoms reported successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@api_view(['GET', 'POST'])
def medical_history_api(request):
    """API endpoint for medical history"""
    if request.method == 'GET':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            history = MedicalHistory.objects.filter(patient=patient_profile).order_by('-updated_at')[:10]
            
            history_data = []
            for record in history:
                history_data.append({
                    'id': record.id,
                    'chronic_conditions': record.chronic_conditions,
                    'past_episodes': record.past_episodes,
                    'updated_at': record.updated_at.isoformat()
                })
            
            return JsonResponse({'success': True, 'history': history_data})
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    
    elif request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            history_data = json.loads(request.body)
            medical_history = MedicalHistoryService.update_medical_history(patient_profile, history_data)
            
            return JsonResponse({
                'success': True,
                'history_id': medical_history.id,
                'message': 'Medical history updated successfully'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@login_required
def risk_assessment_view(request):
    """Display risk assessment dashboard"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        risk_score = RiskAssessmentService.calculate_risk_score(patient_profile)
        
        context = {
            'risk_score': risk_score,
            'patient': patient_profile
        }
        return render(request, 'vitals/risk_assessment.html', context)
    except PatientProfile.DoesNotExist:
        return render(request, 'error.html', {'message': 'Patient profile not found'})


@api_view(['GET', 'POST'])
def risk_assessment_api(request):
    """API endpoint for risk assessments"""
    if request.method == 'GET':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            assessments = RiskAssessment.objects.filter(patient=patient_profile).order_by('-calculated_at')[:10]
            
            assessment_data = []
            for assessment in assessments:
                assessment_data.append({
                    'id': assessment.id,
                    'stability_score': assessment.stability_score,
                    'risk_level': assessment.risk_level,
                    'calculated_at': assessment.calculated_at.isoformat()
                })
            
            return JsonResponse({'success': True, 'assessments': assessment_data})
        except PatientProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    
    elif request.method == 'POST':
        try:
            patient_profile = PatientProfile.objects.get(user=request.user)
            risk_assessment = RiskAssessmentService.calculate_risk_score(patient_profile)
            
            return JsonResponse({
                'success': True,
                'assessment_id': risk_assessment.id,
                'stability_score': risk_assessment.stability_score,
                'risk_level': risk_assessment.risk_level
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})


@api_view(['POST'])
def log_comprehensive_vitals(request):
    """Comprehensive vitals logging API for ML training"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        data = json.loads(request.body)
        
        # Log vital signs
        if 'vitals' in data:
            vital_signs = VitalSignsService.record_vital_signs(patient_profile, data['vitals'])
        
        # Log lifestyle metrics
        if 'lifestyle' in data:
            lifestyle_metrics = LifestyleMetricsService.record_lifestyle_metrics(patient_profile, data['lifestyle'])
        
        # Log symptoms if present
        if 'symptoms' in data:
            symptom_report = SymptomReportService.report_symptoms(patient_profile, data['symptoms'])
        
        # Update medical history if present
        if 'medical_history' in data:
            medical_history = MedicalHistoryService.update_medical_history(patient_profile, data['medical_history'])
        
        # Calculate updated risk score
        risk_assessment = RiskAssessmentService.calculate_risk_score(patient_profile)
        
        return JsonResponse({
            'success': True,
            'message': 'Comprehensive vitals logged successfully',
            'risk_assessment': {
                'stability_score': risk_assessment.stability_score,
                'risk_level': risk_assessment.risk_level
            }
        })
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


class RiskPredictView(APIView):
    """
    API endpoint for LLaMA-powered medical risk prediction
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Predict medical risk using LLaMA 3.2 Medical Pro model
        """
        try:
            # Get current user's patient profile
            patient_profile = PatientProfile.objects.get(user=request.user)
            
            # Validate and serialize input data
            serializer = RiskInputSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    'success': False,
                    'error': 'Invalid input data',
                    'details': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get validated data
            input_data = serializer.validated_data
            
            # ===== DIABETES RISK MODEL INTEGRATION =====
            # Insert diabetes model inference into the diagnosis workflow
            diabetes_result = None
            try:
                from hack_diabetes import get_diabetes_model
                diabetes_model = get_diabetes_model()
                
                # Prepare diabetes model input from patient data
                diabetes_input = {
                    'pregnancies': input_data.get('pregnancies', 0),
                    'glucose': input_data.get('blood_glucose', input_data.get('glucose', 100)),
                    'blood_pressure': input_data.get('systolic', 70),  # Use systolic as primary BP
                    'skin_thickness': input_data.get('skin_thickness', 20),
                    'insulin': input_data.get('insulin', 80),
                    'bmi': input_data.get('bmi', 25),
                    'diabetes_pedigree_function': input_data.get('diabetes_pedigree_function', 0.3),
                    'age': input_data.get('age', patient_profile.age if hasattr(patient_profile, 'age') else 30)
                }
                
                # Get diabetes risk prediction in exact JSON format
                diabetes_result = diabetes_model.predict_diabetes_risk(diabetes_input)
                print(f"🩺 DIABETES MODEL RESULT: {diabetes_result}")  # Debug logging
                
            except Exception as e:
                print(f"⚠️ Diabetes model prediction failed: {e}")
                # Continue with normal workflow if diabetes model fails
                diabetes_result = {
                    "stability_score": 0.5,
                    "diagnosis_label": "Diabetes assessment unavailable",
                    "risk_level": "Low Risk"
                }
            # ===== END DIABETES MODEL INTEGRATION =====
            
            # Initialize LLaMA runner
            from model_runner.llama_runner import LlamaRunner
            llama = LlamaRunner()
            
            # Generate risk prediction using LLaMA (with diabetes context if available)
            prediction_result = llama.predict_medical_risk(input_data, diabetes_context=diabetes_result)
            
            # Store risk assessment in database
            risk_assessment = RiskAssessment.objects.create(
                patient=patient_profile,
                stability_score=prediction_result['stability_score'],
                risk_level=prediction_result['risk_level'],
                risk_percentage=prediction_result['risk_percentage'],
                risk_factors=prediction_result['risk_factors'],
                recommendations=prediction_result['recommendations'],
                assessment_type='llama_prediction'
            )
            
            # ===== DIABETES NUDGE SYSTEM INTEGRATION =====
            # Automatically trigger nudges for Medium/High diabetes risk
            if diabetes_result and diabetes_result['risk_level'] != "Low Risk":
                try:
                    from ai_engine.models import AIHealthNudge
                    from django.utils import timezone
                    from datetime import timedelta
                    
                    # Create diabetes management nudge based on risk level
                    nudge_title = "Diabetes Risk Management"
                    if diabetes_result['risk_level'] == "High Risk":
                        nudge_message = f"Our AI analysis indicates a high diabetes risk (probability: {diabetes_result['stability_score']:.1%}). Consider consulting with your healthcare provider for diabetes screening and preventive care."
                        nudge_priority = "high"
                    else:  # Medium Risk
                        nudge_message = f"Our AI analysis indicates a moderate diabetes risk (probability: {diabetes_result['stability_score']:.1%}). Consider adopting healthy lifestyle habits and regular health monitoring."
                        nudge_priority = "medium"
                    
                    # Create AI health nudge using existing nudge system
                    diabetes_nudge = AIHealthNudge.objects.create(
                        patient=request.user,
                        nudge_type='health_education',
                        title=nudge_title,
                        message=nudge_message,
                        action_suggestion="Schedule healthcare consultation or lifestyle review",
                        model_used='Diabetes SVM + LLaMA Integration',
                        prompt_context={
                            'diabetes_assessment': diabetes_result,
                            'trigger_reason': f'Diabetes risk level: {diabetes_result["risk_level"]}',
                            'assessment_id': risk_assessment.id
                        },
                        patient_history={'diabetes_risk_detected': True},
                        current_context={'risk_level': diabetes_result['risk_level']},
                        behavioral_patterns={'requires_diabetes_monitoring': True},
                        scheduled_for=timezone.now(),
                        expires_at=timezone.now() + timedelta(days=7),  # 7-day expiry
                        delivery_method='dashboard_card'
                    )
                    
                    print(f"🔔 DIABETES NUDGE TRIGGERED: {diabetes_result['risk_level']} - Nudge ID: {diabetes_nudge.id}")  # Debug logging
                    
                except Exception as nudge_error:
                    print(f"⚠️ Failed to create diabetes nudge: {nudge_error}")
                    # Continue execution even if nudge creation fails
            # ===== END DIABETES NUDGE INTEGRATION =====
            
            # Prepare response with diabetes integration
            response_data = {
                'success': True,
                'assessment_id': risk_assessment.id,
                'timestamp': risk_assessment.created_at.isoformat(),
                'risk_prediction': {
                    'stability_score': prediction_result['stability_score'],
                    'risk_level': prediction_result['risk_level'],
                    'risk_percentage': prediction_result['risk_percentage'],
                    'confidence_score': prediction_result.get('confidence_score', 0.85),
                    'risk_factors': prediction_result['risk_factors'],
                    'recommendations': prediction_result['recommendations'],
                    'llama_insights': prediction_result.get('llama_insights', 'Advanced AI analysis completed')
                },
                'diabetes_assessment': diabetes_result,  # Include diabetes model results
                'patient_context': {
                    'patient_id': patient_profile.id,
                    'age': patient_profile.age if hasattr(patient_profile, 'age') else None,
                    'has_medical_history': bool(patient_profile.medical_conditions)
                },
                'nudge_triggered': diabetes_result and diabetes_result['risk_level'] != "Low Risk"  # Indicate if nudge was triggered
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except PatientProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Patient profile not found. Please complete your profile first.'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Risk prediction failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """
        Get historical risk assessments for the current user
        """
        try:
            # Get current user's patient profile
            patient_profile = PatientProfile.objects.get(user=request.user)
            
            # Get recent risk assessments
            recent_assessments = RiskAssessment.objects.filter(
                patient=patient_profile,
                assessment_type='llama_prediction'
            ).order_by('-created_at')[:10]
            
            # Serialize assessments
            assessments_data = []
            for assessment in recent_assessments:
                assessments_data.append({
                    'id': assessment.id,
                    'timestamp': assessment.created_at.isoformat(),
                    'stability_score': assessment.stability_score,
                    'risk_level': assessment.risk_level,
                    'risk_percentage': assessment.risk_percentage,
                    'risk_factors': assessment.risk_factors,
                    'recommendations': assessment.recommendations
                })
            
            return Response({
                'success': True,
                'patient_id': patient_profile.id,
                'total_assessments': len(assessments_data),
                'recent_assessments': assessments_data
            }, status=status.HTTP_200_OK)
            
        except PatientProfile.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Patient profile not found'
            }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': 'Failed to retrieve assessments',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)