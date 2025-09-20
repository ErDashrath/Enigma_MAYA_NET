"""
Clinicians app views - Business logic for clinician management
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import ClinicianProfile, PatientAssignment, ClinicalNote, TreatmentPlan
from patients.models import PatientProfile
from vitals.models import VitalSigns
from ai_engine.models import StabilityScore


class ClinicianProfileService:
    """Business logic for clinician profile management"""
    
    @staticmethod
    def get_clinician_dashboard_data(clinician_profile):
        """Get comprehensive dashboard data for a clinician"""
        # Get assigned patients
        active_assignments = PatientAssignment.objects.filter(
            clinician=clinician_profile,
            status='active'
        ).select_related('patient', 'patient__user')
        
        # Get patient stats
        total_patients = active_assignments.count()
        
        # Get patients requiring attention (high risk or recent alerts)
        high_risk_patients = []
        for assignment in active_assignments:
            latest_score = StabilityScore.objects.filter(
                patient=assignment.patient
            ).order_by('-calculated_at').first()
            
            if latest_score and latest_score.risk_level in ['high', 'critical']:
                high_risk_patients.append({
                    'patient': assignment.patient,
                    'score': latest_score,
                    'assignment': assignment
                })
        
        # Get recent clinical notes
        recent_notes = ClinicalNote.objects.filter(
            clinician=clinician_profile
        ).select_related('patient', 'patient__user').order_by('-created_at')[:10]
        
        # Get active treatment plans
        active_plans = TreatmentPlan.objects.filter(
            clinician=clinician_profile,
            status='active'
        ).select_related('patient', 'patient__user').order_by('-created_at')[:5]
        
        # Get workload statistics
        workload_stats = ClinicianProfileService.calculate_workload_stats(clinician_profile)
        
        return {
            'clinician': clinician_profile,
            'total_patients': total_patients,
            'high_risk_patients': high_risk_patients,
            'recent_notes': recent_notes,
            'active_plans': active_plans,
            'workload_stats': workload_stats,
            'assignments': active_assignments
        }
    
    @staticmethod
    def calculate_workload_stats(clinician_profile):
        """Calculate workload statistics for a clinician"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Count activities in the last week
        notes_this_week = ClinicalNote.objects.filter(
            clinician=clinician_profile,
            created_at__date__gte=week_ago
        ).count()
        
        plans_updated = TreatmentPlan.objects.filter(
            clinician=clinician_profile,
            updated_at__date__gte=week_ago
        ).count()
        
        # Get average patients per day
        active_patients = PatientAssignment.objects.filter(
            clinician=clinician_profile,
            status='active'
        ).count()
        
        # Calculate follow-up reminders
        follow_ups_due = ClinicalNote.objects.filter(
            clinician=clinician_profile,
            follow_up_required=True,
            follow_up_date__lte=timezone.now()
        ).count()
        
        return {
            'notes_this_week': notes_this_week,
            'plans_updated': plans_updated,
            'active_patients': active_patients,
            'follow_ups_due': follow_ups_due,
            'avg_notes_per_patient': round(notes_this_week / max(active_patients, 1), 1)
        }


class PatientAssignmentService:
    """Business logic for patient assignments"""
    
    @staticmethod
    def assign_patient_to_clinician(patient_profile, clinician_profile, assignment_type='primary'):
        """Assign a patient to a clinician"""
        # Check for existing active assignment of same type
        existing = PatientAssignment.objects.filter(
            patient=patient_profile,
            assignment_type=assignment_type,
            status='active'
        ).first()
        
        if existing:
            # Transfer from previous clinician
            existing.status = 'transferred'
            existing.end_date = timezone.now()
            existing.save()
        
        # Create new assignment
        assignment = PatientAssignment.objects.create(
            clinician=clinician_profile,
            patient=patient_profile,
            assignment_type=assignment_type,
            status='active'
        )
        
        return assignment
    
    @staticmethod
    def get_clinician_patients(clinician_profile, assignment_type=None):
        """Get all patients assigned to a clinician"""
        assignments = PatientAssignment.objects.filter(
            clinician=clinician_profile,
            status='active'
        ).select_related('patient', 'patient__user')
        
        if assignment_type:
            assignments = assignments.filter(assignment_type=assignment_type)
        
        return assignments
    
    @staticmethod
    def get_patient_care_team(patient_profile):
        """Get all clinicians assigned to a patient"""
        assignments = PatientAssignment.objects.filter(
            patient=patient_profile,
            status='active'
        ).select_related('clinician', 'clinician__user')
        
        care_team = []
        for assignment in assignments:
            care_team.append({
                'clinician': assignment.clinician,
                'role': assignment.get_assignment_type_display(),
                'assigned_date': assignment.assigned_date
            })
        
        return care_team


class ClinicalNoteService:
    """Business logic for clinical notes"""
    
    @staticmethod
    def create_clinical_note(clinician_profile, patient_profile, note_data):
        """Create a new clinical note"""
        note = ClinicalNote.objects.create(
            clinician=clinician_profile,
            patient=patient_profile,
            note_type=note_data.get('note_type'),
            title=note_data.get('title'),
            content=note_data.get('content'),
            diagnosis_codes=note_data.get('diagnosis_codes', []),
            medications_prescribed=note_data.get('medications_prescribed', []),
            recommendations=note_data.get('recommendations', ''),
            follow_up_required=note_data.get('follow_up_required', False),
            follow_up_date=note_data.get('follow_up_date')
        )
        
        return note
    
    @staticmethod
    def search_patient_notes(patient_profile, clinician_profile=None, note_type=None, query=None):
        """Search clinical notes for a patient"""
        notes = ClinicalNote.objects.filter(patient=patient_profile)
        
        if clinician_profile:
            notes = notes.filter(clinician=clinician_profile)
        
        if note_type:
            notes = notes.filter(note_type=note_type)
        
        if query:
            notes = notes.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(recommendations__icontains=query)
            )
        
        return notes.order_by('-created_at')
    
    @staticmethod
    def get_patient_timeline(patient_profile, days=30):
        """Get chronological timeline of patient care"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get notes in date range
        notes = ClinicalNote.objects.filter(
            patient=patient_profile,
            created_at__gte=start_date
        ).select_related('clinician', 'clinician__user')
        
        # Get vital signs
        vitals = VitalSigns.objects.filter(
            patient=patient_profile,
            recorded_at__gte=start_date
        )
        
        # Combine timeline events
        timeline = []
        
        for note in notes:
            timeline.append({
                'type': 'clinical_note',
                'date': note.created_at,
                'title': note.title,
                'note_type': note.get_note_type_display(),
                'clinician': note.clinician.user.get_full_name(),
                'content': note.content[:200] + '...' if len(note.content) > 200 else note.content
            })
        
        for vital in vitals:
            timeline.append({
                'type': 'vital_signs',
                'date': vital.recorded_at,
                'title': 'Vital Signs Recorded',
                'content': f"BP: {vital.systolic_bp}/{vital.diastolic_bp}, HR: {vital.heart_rate}"
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'], reverse=True)
        
        return timeline


class TreatmentPlanService:
    """Business logic for treatment plans"""
    
    @staticmethod
    def create_treatment_plan(clinician_profile, patient_profile, plan_data):
        """Create a new treatment plan"""
        plan = TreatmentPlan.objects.create(
            clinician=clinician_profile,
            patient=patient_profile,
            title=plan_data.get('title'),
            description=plan_data.get('description'),
            status='draft',
            priority=plan_data.get('priority', 'medium'),
            goals=plan_data.get('goals', []),
            interventions=plan_data.get('interventions', []),
            medications=plan_data.get('medications', []),
            lifestyle_modifications=plan_data.get('lifestyle_modifications', []),
            start_date=plan_data.get('start_date', timezone.now()),
            review_date=plan_data.get('review_date')
        )
        
        return plan
    
    @staticmethod
    def update_plan_progress(plan_id, progress_notes, adherence_score=None):
        """Update treatment plan progress"""
        plan = get_object_or_404(TreatmentPlan, id=plan_id)
        plan.progress_notes = progress_notes
        
        if adherence_score is not None:
            plan.adherence_score = adherence_score
        
        plan.save()
        return plan
    
    @staticmethod
    def get_patient_treatment_history(patient_profile):
        """Get treatment history for a patient"""
        plans = TreatmentPlan.objects.filter(
            patient=patient_profile
        ).select_related('clinician', 'clinician__user').order_by('-created_at')
        
        history = []
        for plan in plans:
            history.append({
                'plan': plan,
                'clinician': plan.clinician.user.get_full_name(),
                'duration': (plan.end_date - plan.start_date).days if plan.end_date else None,
                'status': plan.get_status_display()
            })
        
        return history


# Django views
@login_required
def clinician_dashboard(request):
    """Clinician dashboard view"""
    try:
        clinician_profile = ClinicianProfile.objects.get(user=request.user)
        dashboard_data = ClinicianProfileService.get_clinician_dashboard_data(clinician_profile)
        
        return render(request, 'clinicians/dashboard.html', dashboard_data)
        
    except ClinicianProfile.DoesNotExist:
        return render(request, 'clinicians/create_profile.html')


@login_required
def patient_list(request):
    """List of patients assigned to clinician"""
    try:
        clinician_profile = ClinicianProfile.objects.get(user=request.user)
        
        # Get assignments with search/filter
        assignments = PatientAssignment.objects.filter(
            clinician=clinician_profile,
            status='active'
        ).select_related('patient', 'patient__user')
        
        # Apply filters
        assignment_type = request.GET.get('type')
        search_query = request.GET.get('q')
        
        if assignment_type:
            assignments = assignments.filter(assignment_type=assignment_type)
        
        if search_query:
            assignments = assignments.filter(
                Q(patient__user__first_name__icontains=search_query) |
                Q(patient__user__last_name__icontains=search_query) |
                Q(patient__user__email__icontains=search_query)
            )
        
        # Add risk scores to each patient
        patient_data = []
        for assignment in assignments:
            latest_score = StabilityScore.objects.filter(
                patient=assignment.patient
            ).order_by('-calculated_at').first()
            
            patient_data.append({
                'assignment': assignment,
                'patient': assignment.patient,
                'risk_score': latest_score,
                'last_contact': ClinicalNote.objects.filter(
                    patient=assignment.patient,
                    clinician=clinician_profile
                ).order_by('-created_at').first()
            })
        
        # Pagination
        paginator = Paginator(patient_data, 15)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        return render(request, 'clinicians/patient_list.html', {
            'page_obj': page_obj,
            'assignment_type': assignment_type,
            'search_query': search_query
        })
        
    except ClinicianProfile.DoesNotExist:
        return render(request, 'clinicians/create_profile.html')


@login_required
def patient_detail(request, patient_id):
    """Detailed view of a specific patient"""
    try:
        clinician_profile = ClinicianProfile.objects.get(user=request.user)
        patient_profile = get_object_or_404(PatientProfile, id=patient_id)
        
        # Verify clinician has access to this patient
        assignment = PatientAssignment.objects.filter(
            clinician=clinician_profile,
            patient=patient_profile,
            status='active'
        ).first()
        
        if not assignment:
            return render(request, 'error.html', {
                'message': 'You do not have access to this patient'
            })
        
        # Get comprehensive patient data
        timeline = ClinicalNoteService.get_patient_timeline(patient_profile)
        care_team = PatientAssignmentService.get_patient_care_team(patient_profile)
        treatment_history = TreatmentPlanService.get_patient_treatment_history(patient_profile)
        
        # Get latest stability score
        latest_score = StabilityScore.objects.filter(
            patient=patient_profile
        ).order_by('-calculated_at').first()
        
        return render(request, 'clinicians/patient_detail.html', {
            'patient': patient_profile,
            'assignment': assignment,
            'timeline': timeline,
            'care_team': care_team,
            'treatment_history': treatment_history,
            'stability_score': latest_score
        })
        
    except ClinicianProfile.DoesNotExist:
        return render(request, 'clinicians/create_profile.html')


@login_required
def create_clinical_note(request, patient_id):
    """Create a new clinical note"""
    if request.method == 'POST':
        try:
            clinician_profile = ClinicianProfile.objects.get(user=request.user)
            patient_profile = get_object_or_404(PatientProfile, id=patient_id)
            
            # Verify access
            assignment = PatientAssignment.objects.filter(
                clinician=clinician_profile,
                patient=patient_profile,
                status='active'
            ).first()
            
            if not assignment:
                return JsonResponse({'success': False, 'error': 'Access denied'})
            
            note_data = {
                'note_type': request.POST.get('note_type'),
                'title': request.POST.get('title'),
                'content': request.POST.get('content'),
                'recommendations': request.POST.get('recommendations', ''),
                'follow_up_required': request.POST.get('follow_up_required') == 'on',
                'follow_up_date': request.POST.get('follow_up_date') if request.POST.get('follow_up_date') else None
            }
            
            # Handle JSON fields
            if request.POST.get('diagnosis_codes'):
                note_data['diagnosis_codes'] = request.POST.get('diagnosis_codes').split(',')
            
            if request.POST.get('medications_prescribed'):
                note_data['medications_prescribed'] = request.POST.get('medications_prescribed').split(',')
            
            note = ClinicalNoteService.create_clinical_note(
                clinician_profile, patient_profile, note_data
            )
            
            return JsonResponse({
                'success': True,
                'note_id': note.id,
                'redirect_url': f'/clinicians/patients/{patient_id}/'
            })
            
        except ClinicianProfile.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Clinician profile not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    # GET request - show form
    try:
        clinician_profile = ClinicianProfile.objects.get(user=request.user)
        patient_profile = get_object_or_404(PatientProfile, id=patient_id)
        
        return render(request, 'clinicians/create_note.html', {
            'patient': patient_profile
        })
        
    except ClinicianProfile.DoesNotExist:
        return render(request, 'clinicians/create_profile.html')