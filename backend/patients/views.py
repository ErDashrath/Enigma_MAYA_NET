"""
Patients app views - Business logic for patient management
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import PatientProfile, HealthGoal, PatientNote
from vitals.models import VitalSigns, LifestyleMetrics
from ai_engine.models import StabilityScore


class PatientProfileService:
    """Business logic for patient profile management"""
    
    @staticmethod
    def get_patient_dashboard_data(patient_profile):
        """Get comprehensive dashboard data for a patient"""
        # Get recent vital signs
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at')[:10]
        
        # Get active health goals
        active_goals = HealthGoal.objects.filter(
            patient=patient_profile,
            status='active'
        ).order_by('-created_at')
        
        # Get recent notes
        recent_notes = PatientNote.objects.filter(
            patient=patient_profile
        ).order_by('-created_at')[:5]
        
        # Calculate goal progress summary
        goal_progress = []
        for goal in active_goals:
            progress_percentage = PatientProfileService.calculate_goal_progress(goal)
            goal_progress.append({
                'goal': goal,
                'progress': progress_percentage,
                'status': PatientProfileService.get_goal_status(progress_percentage)
            })
        
        # Get latest stability score
        latest_score = StabilityScore.objects.filter(
            patient=patient_profile
        ).order_by('-calculated_at').first()
        
        return {
            'patient': patient_profile,
            'recent_vitals': recent_vitals,
            'active_goals': goal_progress,
            'recent_notes': recent_notes,
            'stability_score': latest_score,
            'vitals_trend': PatientProfileService.get_vitals_trend(patient_profile),
            'risk_factors': PatientProfileService.get_risk_factors(patient_profile)
        }
    
    @staticmethod
    def calculate_goal_progress(goal):
        """Calculate progress percentage for a health goal"""
        if not goal.target_value or not goal.current_value:
            return 0
        
        if goal.target_value <= 0:
            return 0
        
        # Different calculation based on goal type
        if goal.goal_type in ['weight_loss', 'blood_pressure_reduction']:
            # For reduction goals, progress = (start - current) / (start - target)
            start_value = goal.baseline_value or goal.current_value
            if start_value <= goal.target_value:
                return 100
            progress = ((start_value - goal.current_value) / 
                       (start_value - goal.target_value)) * 100
        else:
            # For improvement goals, progress = current / target
            progress = (goal.current_value / goal.target_value) * 100
        
        return min(max(progress, 0), 100)
    
    @staticmethod
    def get_goal_status(progress_percentage):
        """Determine goal status based on progress"""
        if progress_percentage >= 90:
            return 'excellent'
        elif progress_percentage >= 70:
            return 'good'
        elif progress_percentage >= 50:
            return 'fair'
        else:
            return 'needs_attention'
    
    @staticmethod
    def get_vitals_trend(patient_profile):
        """Get trend analysis for vital signs"""
        # Get last 30 days of vitals
        thirty_days_ago = timezone.now() - timedelta(days=30)
        vitals = VitalSigns.objects.filter(
            patient=patient_profile,
            recorded_at__gte=thirty_days_ago
        ).order_by('recorded_at')
        
        if not vitals.exists():
            return None
        
        # Calculate trends
        first_half = vitals[:len(vitals)//2]
        second_half = vitals[len(vitals)//2:]
        
        trends = {}
        
        if first_half and second_half:
            # Blood pressure trend
            bp_sys_old = first_half.aggregate(Avg('systolic_bp'))['systolic_bp__avg'] or 0
            bp_sys_new = second_half.aggregate(Avg('systolic_bp'))['systolic_bp__avg'] or 0
            trends['blood_pressure'] = 'improving' if bp_sys_new < bp_sys_old else 'worsening'
            
            # Heart rate trend
            hr_old = first_half.aggregate(Avg('heart_rate'))['heart_rate__avg'] or 0
            hr_new = second_half.aggregate(Avg('heart_rate'))['heart_rate__avg'] or 0
            trends['heart_rate'] = 'stable' if abs(hr_new - hr_old) < 5 else ('improving' if hr_new < hr_old else 'concerning')
        
        return trends
    
    @staticmethod
    def get_risk_factors(patient_profile):
        """Identify current risk factors for the patient"""
        risk_factors = []
        
        # Check chronic conditions
        if patient_profile.chronic_conditions:
            for condition in patient_profile.chronic_conditions:
                if condition.lower() in ['diabetes', 'hypertension', 'heart disease']:
                    risk_factors.append(f"Active {condition}")
        
        # Check recent vitals for concerning values
        recent_vitals = VitalSigns.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at').first()
        
        if recent_vitals:
            if recent_vitals.systolic_bp and recent_vitals.systolic_bp > 140:
                risk_factors.append("Elevated blood pressure")
            if recent_vitals.heart_rate and recent_vitals.heart_rate > 100:
                risk_factors.append("Elevated heart rate")
        
        # Check medication adherence
        recent_lifestyle = LifestyleMetrics.objects.filter(
            patient=patient_profile
        ).order_by('-recorded_at').first()
        
        if recent_lifestyle and hasattr(recent_lifestyle, 'medication_adherence'):
            if recent_lifestyle.medication_adherence < 80:
                risk_factors.append("Poor medication adherence")
        
        return risk_factors


class HealthGoalService:
    """Business logic for health goal management"""
    
    @staticmethod
    def create_smart_goal(patient_profile, goal_data):
        """Create a SMART (Specific, Measurable, Achievable, Relevant, Time-bound) goal"""
        # Validate goal parameters
        if not goal_data.get('target_value') or not goal_data.get('target_date'):
            raise ValueError("Goals must have target value and date")
        
        # Set realistic targets based on patient history
        adjusted_target = HealthGoalService.adjust_target_for_realism(
            patient_profile, 
            goal_data['goal_type'], 
            goal_data['target_value']
        )
        
        goal = HealthGoal.objects.create(
            patient=patient_profile,
            goal_type=goal_data['goal_type'],
            title=goal_data['title'],
            description=goal_data.get('description', ''),
            target_value=adjusted_target,
            target_date=goal_data['target_date'],
            baseline_value=goal_data.get('baseline_value'),
            current_value=goal_data.get('baseline_value', 0),
            measurement_unit=goal_data.get('measurement_unit', ''),
            status='active'
        )
        
        return goal
    
    @staticmethod
    def adjust_target_for_realism(patient_profile, goal_type, target_value):
        """Adjust goal targets to be realistic based on patient history"""
        # Get patient's historical data for this goal type
        # This is a simplified version - in practice, you'd use ML models
        
        if goal_type == 'weight_loss':
            # Limit weight loss to 2 lbs per week max
            return min(target_value, 2.0)
        elif goal_type == 'blood_pressure_reduction':
            # Gradual BP reduction
            return max(target_value, 10)  # At least 10 mmHg reduction
        
        return target_value
    
    @staticmethod
    def update_goal_progress(goal_id, new_value):
        """Update goal progress with new measurement"""
        goal = get_object_or_404(HealthGoal, id=goal_id)
        goal.current_value = new_value
        goal.last_updated = timezone.now()
        
        # Check if goal is achieved
        progress = PatientProfileService.calculate_goal_progress(goal)
        if progress >= 95:  # 95% threshold for completion
            goal.status = 'achieved'
            goal.achieved_date = timezone.now()
        
        goal.save()
        return goal


class PatientNoteService:
    """Business logic for patient notes"""
    
    @staticmethod
    def create_automated_note(patient_profile, note_type, data):
        """Create automated notes based on system events"""
        templates = {
            'vital_signs': "Vital signs recorded: BP {systolic}/{diastolic}, HR {heart_rate}, Temp {temperature}°F",
            'goal_progress': "Goal '{goal_title}' updated: {progress}% complete",
            'medication': "Medication adherence: {adherence}%",
            'symptom': "Reported symptoms: {symptoms}"
        }
        
        if note_type not in templates:
            raise ValueError(f"Unknown note type: {note_type}")
        
        content = templates[note_type].format(**data)
        
        note = PatientNote.objects.create(
            patient=patient_profile,
            note_type=note_type,
            title=f"Automated {note_type.replace('_', ' ').title()}",
            content=content,
            is_automated=True
        )
        
        return note
    
    @staticmethod
    def search_notes(patient_profile, query, note_type=None):
        """Search patient notes with filters"""
        notes = PatientNote.objects.filter(patient=patient_profile)
        
        if note_type:
            notes = notes.filter(note_type=note_type)
        
        if query:
            notes = notes.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) |
                Q(tags__contains=[query])
            )
        
        return notes.order_by('-created_at')


# Django views
@login_required
def patient_dashboard(request):
    """Patient dashboard view"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        dashboard_data = PatientProfileService.get_patient_dashboard_data(patient_profile)
        return render(request, 'patients/dashboard.html', dashboard_data)
    except PatientProfile.DoesNotExist:
        return render(request, 'patients/create_profile.html')


@login_required
def health_goals(request):
    """Health goals management view"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        if request.method == 'POST':
            # Create new goal
            goal_data = {
                'goal_type': request.POST.get('goal_type'),
                'title': request.POST.get('title'),
                'description': request.POST.get('description'),
                'target_value': float(request.POST.get('target_value')),
                'target_date': datetime.strptime(request.POST.get('target_date'), '%Y-%m-%d').date(),
                'baseline_value': float(request.POST.get('baseline_value', 0)),
                'measurement_unit': request.POST.get('measurement_unit', '')
            }
            
            goal = HealthGoalService.create_smart_goal(patient_profile, goal_data)
            return JsonResponse({'success': True, 'goal_id': goal.id})
        
        # GET request - show goals
        goals = HealthGoal.objects.filter(patient=patient_profile).order_by('-created_at')
        goal_progress = []
        
        for goal in goals:
            progress = PatientProfileService.calculate_goal_progress(goal)
            goal_progress.append({
                'goal': goal,
                'progress': progress,
                'status': PatientProfileService.get_goal_status(progress)
            })
        
        return render(request, 'patients/health_goals.html', {'goals': goal_progress})
        
    except PatientProfile.DoesNotExist:
        return render(request, 'patients/create_profile.html')


@login_required
def patient_notes(request):
    """Patient notes view"""
    try:
        patient_profile = PatientProfile.objects.get(user=request.user)
        
        # Handle search
        query = request.GET.get('q', '')
        note_type = request.GET.get('type', '')
        
        notes = PatientNoteService.search_notes(patient_profile, query, note_type)
        
        # Pagination
        paginator = Paginator(notes, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'patients/notes.html', {
            'page_obj': page_obj,
            'query': query,
            'note_type': note_type
        })
        
    except PatientProfile.DoesNotExist:
        return render(request, 'patients/create_profile.html')