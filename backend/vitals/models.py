"""
Vitals monitoring models for VitalCircle
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from patients.models import PatientProfile


class VitalSigns(models.Model):
    """Core vital signs measurements"""
    MEASUREMENT_SOURCES = [
        ('manual', 'Manual Entry'),
        ('device', 'Medical Device'),
        ('wearable', 'Wearable Device'),
        ('clinic', 'Clinic Measurement'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='vital_signs')
    
    # Blood Pressure
    systolic_bp = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(60), MaxValueValidator(300)],
        help_text="Systolic blood pressure (mmHg)"
    )
    diastolic_bp = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(200)],
        help_text="Diastolic blood pressure (mmHg)"
    )
    
    # Heart Rate
    heart_rate = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(250)],
        help_text="Heart rate (beats per minute)"
    )
    
    # Temperature
    temperature = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(90.0), MaxValueValidator(110.0)],
        help_text="Body temperature (°F)"
    )
    
    # Weight
    weight = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(50.0), MaxValueValidator(1000.0)],
        help_text="Weight (lbs)"
    )
    
    # Oxygen Saturation
    oxygen_saturation = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(70), MaxValueValidator(100)],
        help_text="Oxygen saturation (%)"
    )
    
    # Respiratory Rate
    respiratory_rate = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(8), MaxValueValidator(40)],
        help_text="Respiratory rate (breaths per minute)"
    )
    
    # Metadata
    measured_at = models.DateTimeField()
    source = models.CharField(max_length=10, choices=MEASUREMENT_SOURCES, default='manual')
    device_info = models.JSONField(default=dict, blank=True, help_text="Device information if applicable")
    notes = models.TextField(blank=True, help_text="Additional notes about measurements")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vitals_signs'
        verbose_name = 'Vital Signs'
        verbose_name_plural = 'Vital Signs'
        ordering = ['-measured_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.measured_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def blood_pressure_reading(self):
        """Return formatted blood pressure reading"""
        if self.systolic_bp and self.diastolic_bp:
            return f"{self.systolic_bp}/{self.diastolic_bp}"
        return None
    
    @property
    def bp_category(self):
        """Categorize blood pressure reading"""
        if not (self.systolic_bp and self.diastolic_bp):
            return "Unknown"
        
        if self.systolic_bp < 120 and self.diastolic_bp < 80:
            return "Normal"
        elif self.systolic_bp < 130 and self.diastolic_bp < 80:
            return "Elevated"
        elif (120 <= self.systolic_bp < 140) or (80 <= self.diastolic_bp < 90):
            return "High Blood Pressure Stage 1"
        elif self.systolic_bp >= 140 or self.diastolic_bp >= 90:
            return "High Blood Pressure Stage 2"
        else:
            return "Hypertensive Crisis"


class LifestyleMetrics(models.Model):
    """Lifestyle and behavioral health metrics"""
    STRESS_LEVELS = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Moderate'),
        (4, 'High'),
        (5, 'Very High'),
    ]
    
    SLEEP_QUALITY = [
        (1, 'Very Poor'),
        (2, 'Poor'),
        (3, 'Fair'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='lifestyle_metrics')
    
    # Stress and Mental Health
    stress_level = models.IntegerField(
        choices=STRESS_LEVELS, null=True, blank=True,
        help_text="Stress level (1-5 scale)"
    )
    mood_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Mood rating (1-10 scale)"
    )
    
    # Sleep
    sleep_hours = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(24.0)],
        help_text="Hours of sleep"
    )
    sleep_quality = models.IntegerField(
        choices=SLEEP_QUALITY, null=True, blank=True,
        help_text="Sleep quality (1-5 scale)"
    )
    
    # Diet and Nutrition
    sodium_intake = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(10000.0)],
        help_text="Sodium intake (mg)"
    )
    water_intake = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(200.0)],
        help_text="Water intake (ounces)"
    )
    calorie_intake = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10000)],
        help_text="Calorie intake"
    )
    
    # Physical Activity
    exercise_minutes = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1440)],
        help_text="Exercise minutes"
    )
    steps_count = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100000)],
        help_text="Daily steps count"
    )
    
    # Medication Adherence
    medication_taken = models.BooleanField(null=True, blank=True, help_text="Medications taken as prescribed")
    missed_doses = models.IntegerField(default=0, help_text="Number of missed medication doses")
    
    recorded_at = models.DateTimeField()
    notes = models.TextField(blank=True, help_text="Additional lifestyle notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vitals_lifestyle_metrics'
        verbose_name = 'Lifestyle Metrics'
        verbose_name_plural = 'Lifestyle Metrics'
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - Lifestyle - {self.recorded_at.strftime('%Y-%m-%d')}"


class SymptomReport(models.Model):
    """Patient-reported symptoms and concerns"""
    SEVERITY_LEVELS = [
        (1, 'Mild'),
        (2, 'Moderate'),
        (3, 'Severe'),
        (4, 'Very Severe'),
        (5, 'Emergency'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='symptom_reports')
    
    symptom_name = models.CharField(max_length=100, help_text="Name of the symptom")
    description = models.TextField(help_text="Detailed description of the symptom")
    severity = models.IntegerField(choices=SEVERITY_LEVELS, help_text="Severity level (1-5)")
    
    # Timing
    onset_time = models.DateTimeField(help_text="When the symptom started")
    duration_hours = models.FloatField(
        null=True, blank=True,
        help_text="Duration of symptom in hours"
    )
    
    # Context
    triggers = models.TextField(blank=True, help_text="Possible triggers")
    relieving_factors = models.TextField(blank=True, help_text="What helps relieve the symptom")
    associated_symptoms = models.TextField(blank=True, help_text="Other related symptoms")
    
    # Follow-up
    resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    follow_up_needed = models.BooleanField(default=False)
    
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vitals_symptom_reports'
        verbose_name = 'Symptom Report'
        verbose_name_plural = 'Symptom Reports'
        ordering = ['-reported_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.symptom_name} (Severity: {self.get_severity_display()})"