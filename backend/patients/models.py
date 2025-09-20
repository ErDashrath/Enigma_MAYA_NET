"""
Patient models for VitalCircle
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class PatientProfile(models.Model):
    """Extended user profile for patients"""
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)
    
    # Medical Information
    chronic_conditions = models.TextField(blank=True, help_text="List of chronic conditions")
    medications = models.TextField(blank=True, help_text="Current medications")
    allergies = models.TextField(blank=True, help_text="Known allergies")
    
    # VitalCircle specific
    current_stability_score = models.FloatField(
        default=0.0, 
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS, default='low')
    last_assessment = models.DateTimeField(auto_now=True)
    
    # Preferences
    notification_preferences = models.JSONField(default=dict, blank=True)
    privacy_settings = models.JSONField(default=dict, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'patient_profiles'
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"
    
    def __str__(self):
        return f"{self.full_name} - {self.get_risk_level_display()}"
    
    class Meta:
        db_table = 'patients_profile'
        verbose_name = 'Patient Profile'
        verbose_name_plural = 'Patient Profiles'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.risk_level}"
    
    @property
    def age(self):
        """Calculate patient's age"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username


class HealthGoal(models.Model):
    """Patient health goals and targets"""
    GOAL_TYPES = [
        ('blood_pressure', 'Blood Pressure'),
        ('weight', 'Weight Management'),
        ('exercise', 'Exercise'),
        ('diet', 'Diet'),
        ('medication', 'Medication Adherence'),
        ('stress', 'Stress Management'),
        ('sleep', 'Sleep Quality'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='health_goals')
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    title = models.CharField(max_length=100)
    description = models.TextField()
    target_value = models.FloatField(help_text="Target value for the goal")
    current_value = models.FloatField(default=0.0, help_text="Current progress value")
    unit = models.CharField(max_length=20, help_text="Unit of measurement")
    
    target_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    progress_percentage = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients_health_goals'
        verbose_name = 'Health Goal'
        verbose_name_plural = 'Health Goals'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.title}"
    
    def calculate_progress(self):
        """Calculate progress percentage"""
        if self.target_value > 0:
            self.progress_percentage = min((self.current_value / self.target_value) * 100, 100)
        return self.progress_percentage


class PatientNote(models.Model):
    """Notes and observations about patients"""
    NOTE_TYPES = [
        ('general', 'General Note'),
        ('symptom', 'Symptom Report'),
        ('medication', 'Medication Note'),
        ('appointment', 'Appointment Note'),
        ('emergency', 'Emergency Note'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='notes')
    note_type = models.CharField(max_length=15, choices=NOTE_TYPES, default='general')
    title = models.CharField(max_length=100)
    content = models.TextField()
    
    # Can be added by patient or clinician
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_private = models.BooleanField(default=False, help_text="Private notes only visible to clinicians")
    
    tags = models.JSONField(default=list, blank=True, help_text="Tags for categorization")
    attachments = models.JSONField(default=list, blank=True, help_text="File attachments metadata")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients_notes'
        verbose_name = 'Patient Note'
        verbose_name_plural = 'Patient Notes'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.title}"