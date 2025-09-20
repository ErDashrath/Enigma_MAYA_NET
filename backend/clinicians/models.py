"""
Clinicians models for VitalCircle - Database definitions only
"""
from django.db import models
from django.contrib.auth.models import User
from patients.models import PatientProfile


class ClinicianProfile(models.Model):
    """Clinician profile extending Django User"""
    SPECIALIZATIONS = [
        ('cardiology', 'Cardiology'),
        ('endocrinology', 'Endocrinology'),
        ('pulmonology', 'Pulmonology'),
        ('nephrology', 'Nephrology'),
        ('general', 'General Medicine'),
        ('nursing', 'Nursing'),
        ('nutrition', 'Nutrition'),
        ('psychology', 'Psychology'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    license_number = models.CharField(max_length=50, unique=True)
    specialization = models.CharField(max_length=20, choices=SPECIALIZATIONS)
    years_experience = models.IntegerField()
    
    # Contact Information
    phone = models.CharField(max_length=20)
    hospital_affiliation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=50, blank=True)
    
    # Professional Details
    medical_degree = models.CharField(max_length=50)
    board_certifications = models.JSONField(default=list)
    languages_spoken = models.JSONField(default=list)
    
    # System Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clinician_profiles'
        verbose_name = 'Clinician Profile'
        verbose_name_plural = 'Clinician Profiles'
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()} - {self.get_specialization_display()}"


class PatientAssignment(models.Model):
    """Assignment of patients to clinicians"""
    ASSIGNMENT_TYPES = [
        ('primary', 'Primary Care Provider'),
        ('specialist', 'Specialist Consultation'),
        ('temporary', 'Temporary Coverage'),
        ('collaborative', 'Collaborative Care'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('transferred', 'Transferred'),
        ('completed', 'Completed'),
    ]
    
    clinician = models.ForeignKey(ClinicianProfile, on_delete=models.CASCADE, related_name='patient_assignments')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='clinician_assignments')
    
    assignment_type = models.CharField(max_length=15, choices=ASSIGNMENT_TYPES)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    
    assigned_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'patient_assignments'
        verbose_name = 'Patient Assignment'
        verbose_name_plural = 'Patient Assignments'
        unique_together = ['clinician', 'patient', 'assignment_type']
    
    def __str__(self):
        return f"{self.clinician.user.get_full_name()} -> {self.patient.full_name} ({self.assignment_type})"


class ClinicalNote(models.Model):
    """Clinical notes and observations"""
    NOTE_TYPES = [
        ('assessment', 'Assessment'),
        ('progress', 'Progress Note'),
        ('treatment', 'Treatment Plan'),
        ('consultation', 'Consultation'),
        ('discharge', 'Discharge Summary'),
        ('follow_up', 'Follow-up'),
    ]
    
    clinician = models.ForeignKey(ClinicianProfile, on_delete=models.CASCADE, related_name='clinical_notes')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='clinical_notes')
    
    note_type = models.CharField(max_length=15, choices=NOTE_TYPES)
    title = models.CharField(max_length=200)
    content = models.TextField()
    
    # Clinical Data
    diagnosis_codes = models.JSONField(default=list, help_text="ICD-10 codes")
    medications_prescribed = models.JSONField(default=list)
    recommendations = models.TextField(blank=True)
    
    # Follow-up
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clinical_notes'
        verbose_name = 'Clinical Note'
        verbose_name_plural = 'Clinical Notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient.full_name} by {self.clinician.user.get_full_name()}"


class TreatmentPlan(models.Model):
    """Treatment plans and care protocols"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('modified', 'Modified'),
        ('completed', 'Completed'),
        ('discontinued', 'Discontinued'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    clinician = models.ForeignKey(ClinicianProfile, on_delete=models.CASCADE, related_name='treatment_plans')
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='treatment_plans')
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Plan Details
    goals = models.JSONField(default=list, help_text="Treatment goals and objectives")
    interventions = models.JSONField(default=list, help_text="Planned interventions")
    medications = models.JSONField(default=list, help_text="Prescribed medications")
    lifestyle_modifications = models.JSONField(default=list, help_text="Lifestyle changes")
    
    # Timeline
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    review_date = models.DateTimeField(help_text="Next review date")
    
    # Progress Tracking
    progress_notes = models.TextField(blank=True)
    adherence_score = models.IntegerField(null=True, blank=True, help_text="Adherence score 0-100")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'treatment_plans'
        verbose_name = 'Treatment Plan'
        verbose_name_plural = 'Treatment Plans'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.patient.full_name}"