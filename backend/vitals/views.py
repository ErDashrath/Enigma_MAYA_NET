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

from .models import VitalSigns, LifestyleMetrics, SymptomReport
from patients.models import PatientProfile, PatientNote
from patients.views import PatientNoteService


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