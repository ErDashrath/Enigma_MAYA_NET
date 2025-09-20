"""
AI Engine views - Business logic for AI predictions and recommendations
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
import json
import random

from .models import (
    StabilityScore, HealthPrediction, SmartNudge, ModelPerformance,
    MedicineAlert, MedicineIntake, AIHealthNudge, WebLLMSession
)
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


# Medicine Alert API Views
@login_required
@csrf_exempt
def medicine_alerts_api(request):
    """API endpoint for medicine alerts CRUD operations"""
    if request.method == 'GET':
        # Get user's medicine alerts
        alerts = MedicineAlert.objects.filter(
            patient=request.user,
            status='active'
        ).order_by('-created_at')
        
        alerts_data = []
        for alert in alerts:
            alerts_data.append({
                'id': alert.id,
                'medicine_name': alert.medicine_name,
                'dosage': alert.dosage,
                'form': alert.form,
                'instructions': alert.instructions,
                'alert_type': alert.alert_type,
                'times_per_day': alert.times_per_day,
                'alert_times': alert.alert_times,
                'priority': alert.priority,
                'start_date': alert.start_date.isoformat(),
                'end_date': alert.end_date.isoformat() if alert.end_date else None,
                'is_enabled': alert.is_enabled,
                'enable_ai_nudges': alert.enable_ai_nudges,
                'created_at': alert.created_at.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'alerts': alerts_data
        })
    
    elif request.method == 'POST':
        # Create new medicine alert
        try:
            data = json.loads(request.body)
            
            alert = MedicineAlert.objects.create(
                patient=request.user,
                medicine_name=data.get('medicine_name'),
                dosage=data.get('dosage'),
                form=data.get('form', 'tablet'),
                instructions=data.get('instructions', ''),
                alert_type=data.get('alert_type', 'daily'),
                times_per_day=data.get('times_per_day', 1),
                alert_times=data.get('alert_times', []),
                priority=data.get('priority', 'medium'),
                reminder_before_minutes=data.get('reminder_before_minutes', 0),
                snooze_duration=data.get('snooze_duration', 15),
                start_date=datetime.strptime(data.get('start_date'), '%Y-%m-%d').date(),
                end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d').date() if data.get('end_date') else None,
                enable_ai_nudges=data.get('enable_ai_nudges', True),
                created_by=request.user
            )
            
            return JsonResponse({
                'success': True,
                'alert_id': alert.id,
                'message': 'Medicine alert created successfully'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
@csrf_exempt
def medicine_alert_detail_api(request, alert_id):
    """API endpoint for individual medicine alert operations"""
    try:
        alert = MedicineAlert.objects.get(
            id=alert_id,
            patient=request.user
        )
    except MedicineAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Medicine alert not found'
        }, status=404)
    
    if request.method == 'GET':
        return JsonResponse({
            'success': True,
            'alert': {
                'id': alert.id,
                'medicine_name': alert.medicine_name,
                'dosage': alert.dosage,
                'form': alert.form,
                'instructions': alert.instructions,
                'alert_type': alert.alert_type,
                'times_per_day': alert.times_per_day,
                'alert_times': alert.alert_times,
                'priority': alert.priority,
                'start_date': alert.start_date.isoformat(),
                'end_date': alert.end_date.isoformat() if alert.end_date else None,
                'status': alert.status,
                'is_enabled': alert.is_enabled,
                'enable_ai_nudges': alert.enable_ai_nudges
            }
        })
    
    elif request.method == 'PUT':
        # Update medicine alert
        try:
            data = json.loads(request.body)
            
            # Update fields
            for field in ['medicine_name', 'dosage', 'form', 'instructions', 
                         'alert_type', 'times_per_day', 'alert_times', 'priority',
                         'is_enabled', 'enable_ai_nudges']:
                if field in data:
                    setattr(alert, field, data[field])
            
            if 'start_date' in data:
                alert.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            
            if 'end_date' in data and data['end_date']:
                alert.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            
            alert.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Medicine alert updated successfully'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    elif request.method == 'DELETE':
        # Delete medicine alert
        alert.status = 'cancelled'
        alert.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Medicine alert cancelled successfully'
        })


@login_required
@csrf_exempt
def record_medicine_intake_api(request):
    """API endpoint to record medicine intake"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            alert = MedicineAlert.objects.get(
                id=data.get('alert_id'),
                patient=request.user
            )
            
            intake = MedicineIntake.objects.create(
                alert=alert,
                patient=request.user,
                scheduled_time=datetime.fromisoformat(data.get('scheduled_time')),
                actual_time=datetime.fromisoformat(data.get('actual_time')) if data.get('actual_time') else timezone.now(),
                status=data.get('status', 'taken'),
                dosage_taken=data.get('dosage_taken', ''),
                notes=data.get('notes', ''),
                side_effects=data.get('side_effects', ''),
                mood_before=data.get('mood_before'),
                mood_after=data.get('mood_after'),
                ai_nudge_used=data.get('ai_nudge_used', False),
                nudge_effectiveness=data.get('nudge_effectiveness')
            )
            
            return JsonResponse({
                'success': True,
                'intake_id': intake.id,
                'message': 'Medicine intake recorded successfully'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
def medicine_intake_history_api(request):
    """API endpoint to get medicine intake history"""
    alert_id = request.GET.get('alert_id')
    days = int(request.GET.get('days', 7))
    
    # Get intake history
    query = MedicineIntake.objects.filter(patient=request.user)
    
    if alert_id:
        query = query.filter(alert_id=alert_id)
    
    since_date = timezone.now() - timedelta(days=days)
    query = query.filter(scheduled_time__gte=since_date)
    
    intakes = query.order_by('-scheduled_time')
    
    intake_data = []
    for intake in intakes:
        intake_data.append({
            'id': intake.id,
            'alert_id': intake.alert.id,
            'medicine_name': intake.alert.medicine_name,
            'scheduled_time': intake.scheduled_time.isoformat(),
            'actual_time': intake.actual_time.isoformat() if intake.actual_time else None,
            'status': intake.status,
            'dosage_taken': intake.dosage_taken,
            'notes': intake.notes,
            'side_effects': intake.side_effects,
            'mood_before': intake.mood_before,
            'mood_after': intake.mood_after,
            'ai_nudge_used': intake.ai_nudge_used
        })
    
    return JsonResponse({
        'success': True,
        'intakes': intake_data
    })


# WebLLM AI Nudge API Views
@login_required
@csrf_exempt
def generate_ai_nudge_api(request):
    """API endpoint to generate AI nudge using WebLLM"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Get medicine alert if specified
            medicine_alert = None
            if data.get('alert_id'):
                medicine_alert = MedicineAlert.objects.get(
                    id=data.get('alert_id'),
                    patient=request.user
                )
            
            # Gather context for AI generation
            context = _gather_patient_context(request.user, medicine_alert)
            
            # Create nudge record
            nudge = AIHealthNudge.objects.create(
                patient=request.user,
                medicine_alert=medicine_alert,
                nudge_type=data.get('nudge_type', 'medicine_reminder'),
                title=data.get('title', 'Health Reminder'),
                message=data.get('message', ''),  # Will be filled by WebLLM
                model_used=data.get('model_used', 'WebLLM-Local'),
                prompt_context=context,
                patient_history=context.get('patient_history', {}),
                current_context=context.get('current_context', {}),
                behavioral_patterns=context.get('behavioral_patterns', {}),
                scheduled_for=timezone.now(),
                expires_at=timezone.now() + timedelta(hours=6),
                delivery_method=data.get('delivery_method', 'dashboard_toast')
            )
            
            return JsonResponse({
                'success': True,
                'nudge_id': nudge.id,
                'context': context,
                'message': 'AI nudge generation initiated'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
@csrf_exempt
def update_ai_nudge_api(request, nudge_id):
    """API endpoint to update AI nudge with generated content"""
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            
            nudge = AIHealthNudge.objects.get(
                id=nudge_id,
                patient=request.user
            )
            
            # Update nudge with AI-generated content
            nudge.message = data.get('message', nudge.message)
            nudge.action_suggestion = data.get('action_suggestion', '')
            nudge.generation_tokens = data.get('generation_tokens', 0)
            nudge.generation_time_ms = data.get('generation_time_ms', 0)
            nudge.status = 'generated'
            
            nudge.save()
            
            return JsonResponse({
                'success': True,
                'message': 'AI nudge updated successfully'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
def get_ai_nudges_api(request):
    """API endpoint to get active AI nudges"""
    # Get active nudges for the user
    nudges = AIHealthNudge.objects.filter(
        patient=request.user,
        status__in=['generated', 'delivered'],
        expires_at__gt=timezone.now()
    ).order_by('-created_at')[:10]
    
    nudges_data = []
    for nudge in nudges:
        nudges_data.append({
            'id': nudge.id,
            'nudge_type': nudge.nudge_type,
            'title': nudge.title,
            'message': nudge.message,
            'action_suggestion': nudge.action_suggestion,
            'delivery_method': nudge.delivery_method,
            'scheduled_for': nudge.scheduled_for.isoformat(),
            'created_at': nudge.created_at.isoformat(),
            'medicine_alert_id': nudge.medicine_alert.id if nudge.medicine_alert else None
        })
    
    return JsonResponse({
        'success': True,
        'nudges': nudges_data
    })


@login_required
@csrf_exempt
def nudge_interaction_api(request, nudge_id):
    """API endpoint to track nudge interactions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            nudge = AIHealthNudge.objects.get(
                id=nudge_id,
                patient=request.user
            )
            
            interaction_type = data.get('interaction_type')
            
            if interaction_type == 'viewed':
                nudge.viewed_at = timezone.now()
                nudge.status = 'viewed'
            elif interaction_type == 'acted_upon':
                nudge.acted_upon_at = timezone.now()
                nudge.status = 'acted_upon'
                nudge.led_to_action = True
                nudge.action_type = data.get('action_type', '')
            elif interaction_type == 'dismissed':
                nudge.status = 'dismissed'
            
            if data.get('user_rating'):
                nudge.user_rating = data.get('user_rating')
            
            nudge.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Nudge interaction recorded'
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


@login_required
@csrf_exempt
def webllm_session_api(request):
    """API endpoint to track WebLLM usage sessions"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            if data.get('action') == 'start':
                # Start new session
                session = WebLLMSession.objects.create(
                    patient=request.user,
                    session_type=data.get('session_type', 'general_chat'),
                    model_id=data.get('model_id', ''),
                    model_size=data.get('model_size', ''),
                    initial_prompt=data.get('initial_prompt', ''),
                    browser_info=data.get('browser_info', {}),
                    device_info=data.get('device_info', {})
                )
                
                return JsonResponse({
                    'success': True,
                    'session_id': session.id
                })
            
            elif data.get('action') == 'end':
                # End existing session
                session = WebLLMSession.objects.get(
                    id=data.get('session_id'),
                    patient=request.user
                )
                
                session.session_end = timezone.now()
                session.total_messages = data.get('total_messages', 0)
                session.total_tokens_generated = data.get('total_tokens_generated', 0)
                session.average_response_time_ms = data.get('average_response_time_ms', 0)
                session.total_generation_time_ms = data.get('total_generation_time_ms', 0)
                session.conversation_summary = data.get('conversation_summary', '')
                session.user_rating = data.get('user_rating')
                session.feedback = data.get('feedback', '')
                session.performance_stats = data.get('performance_stats', {})
                
                session.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Session ended successfully'
                })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)


def _gather_patient_context(user, medicine_alert=None):
    """Helper function to gather patient context for AI nudge generation"""
    context = {
        'patient_history': {},
        'current_context': {},
        'behavioral_patterns': {}
    }
    
    # Get recent medicine intake history
    if medicine_alert:
        recent_intakes = MedicineIntake.objects.filter(
            alert=medicine_alert,
            scheduled_time__gte=timezone.now() - timedelta(days=7)
        )
        
        total_scheduled = recent_intakes.count()
        taken_count = recent_intakes.filter(status='taken').count()
        adherence_rate = (taken_count / total_scheduled * 100) if total_scheduled > 0 else 100
        
        context['patient_history']['adherence_rate'] = adherence_rate
        context['patient_history']['recent_missed'] = recent_intakes.filter(status='missed').count()
        context['patient_history']['total_scheduled'] = total_scheduled
        
        # Get last intake
        last_intake = recent_intakes.order_by('-scheduled_time').first()
        if last_intake:
            context['current_context']['last_intake_status'] = last_intake.status
            context['current_context']['days_since_last_intake'] = (timezone.now() - last_intake.scheduled_time).days
    
    # Get general health patterns
    try:
        from patients.models import PatientProfile
        patient_profile = PatientProfile.objects.get(user=user)
        context['patient_history']['chronic_conditions'] = getattr(patient_profile, 'chronic_conditions', [])
    except PatientProfile.DoesNotExist:
        pass
    
    # Current time context
    current_hour = timezone.now().hour
    if current_hour < 12:
        context['current_context']['time_of_day'] = 'morning'
    elif current_hour < 17:
        context['current_context']['time_of_day'] = 'afternoon'
    elif current_hour < 21:
        context['current_context']['time_of_day'] = 'evening'
    else:
        context['current_context']['time_of_day'] = 'night'
    
    return context