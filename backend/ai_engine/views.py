"""
AI Engine views - Business logic for AI predictions and recommendations
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import random

from .models import StabilityScore, HealthPrediction, SmartNudge, ModelPerformance
from patients.models import PatientProfile
from vitals.models import VitalSigns, LifestyleMetrics


class StabilityScoreService:
    """Business logic for calculating and managing stability scores"""
    
    @staticmethod
    def calculate_stability_score(patient_profile):
        """Calculate comprehensive stability score for a patient"""
        # Get recent data (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Get recent vitals and lifestyle metrics
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile,
            recorded_at__gte=seven_days_ago
        )
        
        recent_lifestyle = LifestyleMetrics.objects.filter(
            patient=patient_profile,
            recorded_at__gte=seven_days_ago
        )
        
        # Calculate component scores
        vital_signs_score = StabilityScoreService._calculate_vitals_score(recent_vitals)
        lifestyle_score = StabilityScoreService._calculate_lifestyle_score(recent_lifestyle)
        medication_score = StabilityScoreService._calculate_medication_score(recent_lifestyle)
        symptom_score = StabilityScoreService._calculate_symptom_score(patient_profile)
        
        # Weighted overall score
        weights = {
            'vitals': 0.35,
            'lifestyle': 0.25,
            'medication': 0.25,
            'symptoms': 0.15
        }
        
        overall_score = (
            vital_signs_score * weights['vitals'] +
            lifestyle_score * weights['lifestyle'] +
            medication_score * weights['medication'] +
            symptom_score * weights['symptoms']
        )
        
        # Determine risk level
        risk_level = StabilityScoreService._determine_risk_level(overall_score)
        
        # Identify specific risks
        identified_risks = StabilityScoreService._identify_risks(
            patient_profile, recent_vitals, recent_lifestyle
        )
        
        # Calculate risk probability
        risk_probability = max(0, (100 - overall_score) / 100)
        
        # Create or update stability score
        stability_score = StabilityScore.objects.create(
            patient=patient_profile,
            score=round(overall_score, 1),
            risk_level=risk_level,
            vital_signs_score=round(vital_signs_score, 1),
            lifestyle_score=round(lifestyle_score, 1),
            medication_adherence_score=round(medication_score, 1),
            symptom_burden_score=round(symptom_score, 1),
            identified_risks=identified_risks,
            risk_probability=round(risk_probability, 3),
            model_version="1.0",
            calculation_method="rule_based",
            confidence_level=0.85,
            data_freshness=timezone.now()
        )
        
        return stability_score
    
    @staticmethod
    def _calculate_vitals_score(recent_vitals):
        """Calculate vital signs component score"""
        if not recent_vitals.exists():
            return 50.0  # Neutral score for missing data
        
        score = 100.0
        vitals_avg = recent_vitals.aggregate(
            avg_systolic=Avg('systolic_bp'),
            avg_diastolic=Avg('diastolic_bp'),
            avg_heart_rate=Avg('heart_rate'),
            avg_temperature=Avg('temperature')
        )
        
        # Blood pressure scoring
        systolic = vitals_avg.get('avg_systolic')
        diastolic = vitals_avg.get('avg_diastolic')
        
        if systolic and diastolic:
            if systolic > 140 or diastolic > 90:
                score -= 25
            elif systolic > 130 or diastolic > 85:
                score -= 15
            elif systolic < 90 or diastolic < 60:
                score -= 20
        
        # Heart rate scoring
        heart_rate = vitals_avg.get('avg_heart_rate')
        if heart_rate:
            if heart_rate > 100 or heart_rate < 60:
                score -= 15
        
        return max(0, score)
    
    @staticmethod
    def _calculate_lifestyle_score(recent_lifestyle):
        """Calculate lifestyle component score"""
        if not recent_lifestyle.exists():
            return 50.0
        
        lifestyle_avg = recent_lifestyle.aggregate(
            avg_stress=Avg('stress_level'),
            avg_sleep_hours=Avg('sleep_hours'),
            avg_sleep_quality=Avg('sleep_quality'),
            avg_exercise=Avg('exercise_minutes'),
            avg_diet_quality=Avg('diet_quality')
        )
        
        score = 100.0
        
        # Stress level impact
        stress = lifestyle_avg.get('avg_stress')
        if stress:
            if stress >= 4:
                score -= 20
            elif stress >= 3:
                score -= 10
        
        # Sleep impact
        sleep_hours = lifestyle_avg.get('avg_sleep_hours')
        if sleep_hours:
            if sleep_hours < 6 or sleep_hours > 9:
                score -= 15
        
        sleep_quality = lifestyle_avg.get('avg_sleep_quality')
        if sleep_quality and sleep_quality < 3:
            score -= 10
        
        # Exercise impact
        exercise = lifestyle_avg.get('avg_exercise')
        if exercise:
            if exercise < 30:  # Less than 30 minutes
                score -= 10
        
        return max(0, score)
    
    @staticmethod
    def _calculate_medication_score(recent_lifestyle):
        """Calculate medication adherence score"""
        if not recent_lifestyle.exists():
            return 80.0  # Assume good adherence if no data
        
        adherence_avg = recent_lifestyle.aggregate(
            avg_adherence=Avg('medication_adherence')
        ).get('avg_adherence')
        
        if adherence_avg is None:
            return 80.0
        
        return adherence_avg
    
    @staticmethod
    def _calculate_symptom_score(patient_profile):
        """Calculate symptom burden score"""
        # Get recent symptom reports (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        from vitals.models import SymptomReport
        recent_symptoms = SymptomReport.objects.filter(
            patient=patient_profile,
            reported_at__gte=seven_days_ago
        )
        
        if not recent_symptoms.exists():
            return 100.0  # No symptoms reported
        
        # Calculate based on frequency and severity
        avg_severity = recent_symptoms.aggregate(
            avg_severity=Avg('severity_level')
        ).get('avg_severity', 1)
        
        symptom_count = recent_symptoms.count()
        
        # Base score starts at 100, reduces based on symptoms
        score = 100 - (avg_severity * 10) - (symptom_count * 5)
        
        return max(0, score)
    
    @staticmethod
    def _determine_risk_level(score):
        """Determine risk level based on stability score"""
        if score >= 80:
            return 'low'
        elif score >= 60:
            return 'medium'
        elif score >= 40:
            return 'high'
        else:
            return 'critical'
    
    @staticmethod
    def _identify_risks(patient_profile, recent_vitals, recent_lifestyle):
        """Identify specific risk factors"""
        risks = []
        
        # Check chronic conditions
        if patient_profile.chronic_conditions:
            for condition in patient_profile.chronic_conditions:
                if condition.lower() in ['diabetes', 'hypertension', 'heart disease']:
                    risks.append(f"chronic_{condition.lower().replace(' ', '_')}")
        
        # Check vital signs patterns
        if recent_vitals.exists():
            vitals_avg = recent_vitals.aggregate(
                avg_systolic=Avg('systolic_bp'),
                avg_diastolic=Avg('diastolic_bp'),
                avg_heart_rate=Avg('heart_rate')
            )
            
            if vitals_avg.get('avg_systolic', 0) > 140:
                risks.append('elevated_blood_pressure')
            
            if vitals_avg.get('avg_heart_rate', 0) > 100:
                risks.append('elevated_heart_rate')
        
        # Check lifestyle factors
        if recent_lifestyle.exists():
            lifestyle_avg = recent_lifestyle.aggregate(
                avg_stress=Avg('stress_level'),
                avg_adherence=Avg('medication_adherence')
            )
            
            if lifestyle_avg.get('avg_stress', 0) >= 4:
                risks.append('high_stress_levels')
            
            if lifestyle_avg.get('avg_adherence', 100) < 80:
                risks.append('poor_medication_adherence')
        
        return risks


class HealthPredictionService:
    """Business logic for health predictions"""
    
    @staticmethod
    def generate_predictions(patient_profile):
        """Generate health predictions for a patient"""
        predictions = []
        
        # Get recent data for analysis
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at')[:10]
        
        recent_lifestyle = LifestyleMetrics.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at')[:7]
        
        # Blood pressure spike prediction
        bp_prediction = HealthPredictionService._predict_bp_spike(
            patient_profile, recent_vitals, recent_lifestyle
        )
        if bp_prediction:
            predictions.append(bp_prediction)
        
        # Medication adherence prediction
        med_prediction = HealthPredictionService._predict_medication_nonadherence(
            patient_profile, recent_lifestyle
        )
        if med_prediction:
            predictions.append(med_prediction)
        
        # General health deterioration prediction
        health_prediction = HealthPredictionService._predict_health_deterioration(
            patient_profile, recent_vitals, recent_lifestyle
        )
        if health_prediction:
            predictions.append(health_prediction)
        
        return predictions
    
    @staticmethod
    def _predict_bp_spike(patient_profile, recent_vitals, recent_lifestyle):
        """Predict blood pressure spike risk"""
        if not recent_vitals.exists():
            return None
        
        # Calculate trend
        vitals_list = list(recent_vitals.values('systolic_bp', 'recorded_at'))
        if len(vitals_list) < 3:
            return None
        
        # Simple trend analysis (in practice, use ML models)
        recent_avg = sum(v['systolic_bp'] for v in vitals_list[:3] if v['systolic_bp']) / 3
        older_avg = sum(v['systolic_bp'] for v in vitals_list[-3:] if v['systolic_bp']) / 3
        
        trend_increase = recent_avg - older_avg
        
        # Risk factors
        risk_factors = 0
        if trend_increase > 10:
            risk_factors += 1
        
        if recent_lifestyle.exists():
            lifestyle_avg = recent_lifestyle.aggregate(avg_stress=Avg('stress_level')).get('avg_stress', 0)
            if lifestyle_avg >= 4:
                risk_factors += 1
        
        if patient_profile.chronic_conditions and 'hypertension' in patient_profile.chronic_conditions:
            risk_factors += 1
        
        # Calculate probability
        base_probability = 0.15  # 15% base risk
        probability = min(0.95, base_probability + (risk_factors * 0.15))
        
        if probability > 0.3:  # Only create prediction if significant risk
            return HealthPrediction.objects.create(
                patient=patient_profile,
                prediction_type='blood_pressure_spike',
                time_horizon='7d',
                probability=probability,
                confidence=0.75,
                description=f"Elevated risk of blood pressure spike based on recent trend (+{trend_increase:.1f} mmHg)",
                key_factors=['blood_pressure_trend', 'stress_level', 'chronic_conditions'],
                model_name='BP_Predictor',
                model_version='1.0',
                expires_at=timezone.now() + timedelta(days=7)
            )
        
        return None


class SmartNudgeService:
    """Business logic for personalized health nudges"""
    
    @staticmethod
    def generate_personalized_nudges(patient_profile):
        """Generate personalized health nudges based on patient data"""
        nudges = []
        
        # Get recent data
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at').first()
        
        recent_lifestyle = LifestyleMetrics.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at').first()
        
        # Medication reminder nudges
        if recent_lifestyle and recent_lifestyle.medication_adherence < 80:
            nudges.append(SmartNudgeService._create_medication_nudge(patient_profile))
        
        # Exercise nudges
        if recent_lifestyle and (not recent_lifestyle.exercise_minutes or recent_lifestyle.exercise_minutes < 30):
            nudges.append(SmartNudgeService._create_exercise_nudge(patient_profile))
        
        # Sleep hygiene nudges
        if recent_lifestyle and (not recent_lifestyle.sleep_hours or recent_lifestyle.sleep_hours < 7):
            nudges.append(SmartNudgeService._create_sleep_nudge(patient_profile))
        
        # Stress management nudges
        if recent_lifestyle and recent_lifestyle.stress_level >= 4:
            nudges.append(SmartNudgeService._create_stress_nudge(patient_profile))
        
        # Vital signs monitoring nudges
        if not recent_vitals or (timezone.now() - recent_vitals.recorded_at).days > 3:
            nudges.append(SmartNudgeService._create_monitoring_nudge(patient_profile))
        
        # Filter out None values and return
        return [nudge for nudge in nudges if nudge is not None]
    
    @staticmethod
    def _create_medication_nudge(patient_profile):
        """Create medication adherence nudge"""
        return SmartNudge.objects.create(
            patient=patient_profile,
            category='medication',
            priority='high',
            title='Medication Reminder',
            message='Your medication adherence has decreased. Consistent medication use is crucial for managing your health condition.',
            action_text='Set Reminders',
            target_behavior='medication_adherence',
            personalization_factors={'recent_adherence': 'below_target'},
            delivery_method='dashboard',
            expires_at=timezone.now() + timedelta(days=3)
        )
    
    @staticmethod
    def _create_exercise_nudge(patient_profile):
        """Create exercise recommendation nudge"""
        return SmartNudge.objects.create(
            patient=patient_profile,
            category='exercise',
            priority='medium',
            title='Stay Active',
            message='Regular physical activity can help improve your cardiovascular health. Even a 15-minute walk can make a difference!',
            action_text='Log Activity',
            target_behavior='physical_activity',
            personalization_factors={'activity_level': 'low'},
            delivery_method='dashboard',
            expires_at=timezone.now() + timedelta(days=2)
        )


# Django views
@login_required
def ai_dashboard(request):
    """AI insights dashboard"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        # Get or calculate latest stability score
        latest_score = StabilityScore.objects.filter(
            patient=patient_profile
        ).order_by('-calculated_at').first()
        
        if not latest_score or (timezone.now() - latest_score.calculated_at).hours > 24:
            # Calculate new score if older than 24 hours
            latest_score = StabilityScoreService.calculate_stability_score(patient_profile)
        
        # Get recent predictions
        recent_predictions = HealthPrediction.objects.filter(
            patient=patient_profile,
            expires_at__gt=timezone.now()
        ).order_by('-created_at')[:5]
        
        # Get active nudges
        active_nudges = SmartNudge.objects.filter(
            patient=patient_profile,
            expires_at__gt=timezone.now(),
            dismissed_at__isnull=True
        ).order_by('-priority', '-created_at')[:5]
        
        return render(request, 'ai_engine/dashboard.html', {
            'stability_score': latest_score,
            'predictions': recent_predictions,
            'nudges': active_nudges
        })
        
    except PatientProfile.DoesNotExist:
        return render(request, 'patients/create_profile.html')


@login_required
def calculate_stability(request):
    """API endpoint to calculate new stability score"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        stability_score = StabilityScoreService.calculate_stability_score(patient_profile)
        
        return JsonResponse({
            'success': True,
            'score': stability_score.score,
            'risk_level': stability_score.risk_level,
            'components': {
                'vitals': stability_score.vital_signs_score,
                'lifestyle': stability_score.lifestyle_score,
                'medication': stability_score.medication_adherence_score,
                'symptoms': stability_score.symptom_burden_score
            },
            'risks': stability_score.identified_risks
        })
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})


@login_required
def generate_predictions(request):
    """API endpoint to generate new health predictions"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        predictions = HealthPredictionService.generate_predictions(patient_profile)
        
        predictions_data = []
        for prediction in predictions:
            predictions_data.append({
                'type': prediction.get_prediction_type_display(),
                'probability': prediction.probability,
                'time_horizon': prediction.get_time_horizon_display(),
                'description': prediction.description
            })
        
        return JsonResponse({
            'success': True,
            'predictions': predictions_data
        })
        
    except PatientProfile.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Patient profile not found'})