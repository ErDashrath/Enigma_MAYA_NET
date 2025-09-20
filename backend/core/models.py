"""
VitalCircle Models for Chronic Care Management
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime


class UserProfile(models.Model):
    """Extended user profile for all users"""
    USER_TYPES = [
        ('patient', 'Patient'),
        ('clinician', 'Clinician'),
        ('admin', 'Administrator'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='patient')
    phone_number = models.CharField(max_length=15, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_user_type_display()})"


class PatientProfile(models.Model):
    """Extended user profile for patients"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='patient_profile')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    medical_conditions = models.TextField(blank=True, help_text="Comma-separated chronic conditions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username}'s Profile"


class VitalSigns(models.Model):
    """Patient vital signs records"""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vital_signs')
    
    # Blood Pressure
    systolic_bp = models.IntegerField(
        validators=[MinValueValidator(60), MaxValueValidator(300)],
        help_text="Systolic blood pressure (mmHg)"
    )
    diastolic_bp = models.IntegerField(
        validators=[MinValueValidator(40), MaxValueValidator(200)],
        help_text="Diastolic blood pressure (mmHg)"
    )
    
    # Heart Rate
    heart_rate = models.IntegerField(
        validators=[MinValueValidator(30), MaxValueValidator(220)],
        help_text="Heart rate (beats per minute)"
    )
    
    # Stress Level (1-10 scale)
    stress_level = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Stress level on scale of 1-10"
    )
    
    # Sodium Intake
    sodium_intake = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        help_text="Daily sodium intake (mg)"
    )
    
    # Additional metrics
    weight = models.FloatField(null=True, blank=True, help_text="Weight in kg")
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        verbose_name_plural = "Vital Signs"

    def __str__(self):
        return f"{self.patient.username} - {self.recorded_at.strftime('%Y-%m-%d %H:%M')}"

    @property
    def blood_pressure(self):
        return f"{self.systolic_bp}/{self.diastolic_bp}"


class StabilityScore(models.Model):
    """AI-generated stability scores for patients"""
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stability_scores')
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Stability score (0-100)"
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    
    # Factors contributing to the score
    bp_factor = models.FloatField(default=0, help_text="Blood pressure contribution")
    hr_factor = models.FloatField(default=0, help_text="Heart rate contribution")
    stress_factor = models.FloatField(default=0, help_text="Stress level contribution")
    sodium_factor = models.FloatField(default=0, help_text="Sodium intake contribution")
    
    recommendations = models.JSONField(default=list, help_text="AI-generated recommendations")
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-calculated_at']

    def __str__(self):
        return f"{self.patient.username} - Score: {self.score} ({self.risk_level})"


class HealthNudge(models.Model):
    """AI-generated health nudges and recommendations"""
    NUDGE_TYPES = [
        ('nutrition', 'Nutrition'),
        ('exercise', 'Exercise'),
        ('medication', 'Medication'),
        ('lifestyle', 'Lifestyle'),
        ('monitoring', 'Monitoring'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='health_nudges')
    nudge_type = models.CharField(max_length=20, choices=NUDGE_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Priority level (1=lowest, 5=highest)"
    )
    
    is_read = models.BooleanField(default=False)
    is_dismissed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-priority', '-created_at']

    def __str__(self):
        return f"{self.patient.username} - {self.title}"


class ClinicianNote(models.Model):
    """Notes from healthcare providers"""
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clinician_notes')
    clinician = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notes')
    title = models.CharField(max_length=200)
    content = models.TextField()
    is_urgent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Note for {self.patient.username} by {self.clinician.username}"
