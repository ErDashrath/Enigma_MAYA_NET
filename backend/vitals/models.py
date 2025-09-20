"""
Vitals monitoring models for VitalCircle
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
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
    
    # Height (for BMI calculation)
    height = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(36.0), MaxValueValidator(96.0)],
        help_text="Height (inches)"
    )
    
    # Blood Glucose
    blood_glucose = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(40), MaxValueValidator(600)],
        help_text="Blood glucose level (mg/dL)"
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
    def bmi(self):
        """Calculate BMI from weight and height"""
        if self.weight and self.height:
            # BMI = (weight in lbs / (height in inches)²) × 703
            return round((self.weight / (self.height ** 2)) * 703, 1)
        return None
    
    @property
    def bmi_category(self):
        """Categorize BMI reading"""
        bmi = self.bmi
        if not bmi:
            return "Unknown"
        
        if bmi < 18.5:
            return "Underweight"
        elif bmi < 25:
            return "Normal weight"
        elif bmi < 30:
            return "Overweight"
        else:
            return "Obese"
    
    @property
    def glucose_category(self):
        """Categorize blood glucose reading"""
        if not self.blood_glucose:
            return "Unknown"
        
        if self.blood_glucose < 70:
            return "Low (Hypoglycemia)"
        elif self.blood_glucose < 100:
            return "Normal (Fasting)"
        elif self.blood_glucose < 140:
            return "Pre-diabetes"
        else:
            return "Diabetes Range"
    
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
    
    ACTIVITY_LEVELS = [
        (1, 'Sedentary'),
        (2, 'Lightly Active'),
        (3, 'Moderately Active'),
        (4, 'Very Active'),
        (5, 'Extra Active'),
    ]
    
    FOOD_CATEGORIES = [
        ('vegetables', 'Vegetables'),
        ('fruits', 'Fruits'),
        ('grains', 'Grains'),
        ('protein', 'Protein'),
        ('dairy', 'Dairy'),
        ('processed', 'Processed Foods'),
        ('fast_food', 'Fast Food'),
        ('sweets', 'Sweets/Desserts'),
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
    
    # Food log categories (JSON field to track multiple food types)
    food_log = models.JSONField(
        default=dict,
        blank=True,
        help_text="Daily food intake by category {category: servings}"
    )
    
    # Physical Activity
    activity_level = models.IntegerField(
        choices=ACTIVITY_LEVELS, null=True, blank=True,
        help_text="Overall activity level (1-5 scale)"
    )
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
    medication_adherence_percentage = models.FloatField(
        null=True, blank=True,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Medication adherence percentage (0-100%)"
    )
    
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
    
    @property
    def stress_level_display(self):
        """Get human-readable stress level"""
        return dict(self.STRESS_LEVELS).get(self.stress_level, "Unknown")
    
    @property
    def activity_level_display(self):
        """Get human-readable activity level"""
        return dict(self.ACTIVITY_LEVELS).get(self.activity_level, "Unknown")
    
    @property
    def total_food_servings(self):
        """Calculate total food servings from food log"""
        if not self.food_log:
            return 0
        return sum(self.food_log.values())


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


class MedicalHistory(models.Model):
    """Track chronic conditions, past episodes, and medical history"""
    CHRONIC_CONDITIONS = [
        ('hypertension', 'Hypertension'),
        ('diabetes_type1', 'Type 1 Diabetes'),
        ('diabetes_type2', 'Type 2 Diabetes'),
        ('heart_disease', 'Heart Disease'),
        ('stroke', 'Stroke'),
        ('kidney_disease', 'Kidney Disease'),
        ('liver_disease', 'Liver Disease'),
        ('copd', 'COPD'),
        ('asthma', 'Asthma'),
        ('cancer', 'Cancer'),
        ('depression', 'Depression'),
        ('anxiety', 'Anxiety'),
        ('other', 'Other'),
    ]
    
    EPISODE_TYPES = [
        ('hypertensive_crisis', 'Hypertensive Crisis'),
        ('hypoglycemia', 'Hypoglycemia (Low Blood Sugar)'),
        ('hyperglycemia', 'Hyperglycemia (High Blood Sugar)'),
        ('heart_attack', 'Heart Attack'),
        ('stroke', 'Stroke'),
        ('emergency_room', 'Emergency Room Visit'),
        ('hospitalization', 'Hospitalization'),
        ('medication_reaction', 'Medication Adverse Reaction'),
        ('fall', 'Fall/Injury'),
        ('other', 'Other Medical Episode'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='medical_history')
    
    # Chronic Conditions
    chronic_conditions = models.JSONField(
        default=list,
        help_text="List of chronic conditions patient has"
    )
    
    # Past Episodes
    past_episodes = models.JSONField(
        default=list,
        help_text="List of past medical episodes with dates and details"
    )
    
    # Family History
    family_history = models.JSONField(
        default=dict,
        blank=True,
        help_text="Family medical history by condition"
    )
    
    # Risk Factors
    risk_factors = models.JSONField(
        default=list,
        help_text="Additional risk factors (smoking, alcohol, etc.)"
    )
    
    # Allergies and Reactions
    allergies = models.JSONField(
        default=list,
        help_text="Known allergies and adverse reactions"
    )
    
    # Current Medications
    current_medications = models.JSONField(
        default=list,
        help_text="List of current medications with dosages"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Additional medical history notes")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vitals_medical_history'
        verbose_name = 'Medical History'
        verbose_name_plural = 'Medical Histories'
        ordering = ['-updated_at']
    
    def __str__(self):
        conditions = ', '.join(self.chronic_conditions) if self.chronic_conditions else 'No conditions'
        return f"{self.patient.full_name} - Medical History ({conditions})"
    
    def has_condition(self, condition):
        """Check if patient has a specific chronic condition"""
        return condition in self.chronic_conditions
    
    def has_diabetes(self):
        """Check if patient has any type of diabetes"""
        return any(condition in self.chronic_conditions for condition in ['diabetes_type1', 'diabetes_type2'])
    
    def add_episode(self, episode_type, date, description="", severity=None):
        """Add a new medical episode"""
        episode = {
            'type': episode_type,
            'date': date.isoformat() if hasattr(date, 'isoformat') else str(date),
            'description': description,
            'severity': severity,
            'recorded_at': timezone.now().isoformat()
        }
        if not self.past_episodes:
            self.past_episodes = []
        self.past_episodes.append(episode)
        self.save()


class RiskAssessment(models.Model):
    """ML-based risk assessments and predictions for adverse events"""
    RISK_LEVELS = [
        ('low', 'Low Risk (0-25%)'),
        ('moderate', 'Moderate Risk (25-50%)'),
        ('high', 'High Risk (50-75%)'),
        ('critical', 'Critical Risk (75-100%)'),
    ]
    
    TIME_HORIZONS = [
        ('24h', 'Next 24 Hours'),
        ('48h', 'Next 48 Hours'),
        ('7d', 'Next 7 Days'),
        ('30d', 'Next 30 Days'),
    ]
    
    ASSESSMENT_TYPES = [
        ('manual', 'Manual Assessment'),
        ('automated', 'Automated Assessment'),
        ('llama_prediction', 'LLaMA AI Prediction'),
        ('rule_based', 'Rule-Based Assessment'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='risk_assessments')
    
    # Assessment Type
    assessment_type = models.CharField(
        max_length=20, 
        choices=ASSESSMENT_TYPES, 
        default='automated',
        help_text="Type of risk assessment performed"
    )
    
    # Core Assessment
    stability_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Stability score (0-100, higher is more stable)"
    )
    
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    time_horizon = models.CharField(max_length=5, choices=TIME_HORIZONS, default='48h')
    
    # Risk of adverse event (binary prediction)
    adverse_event_risk = models.BooleanField(
        help_text="High risk of adverse event in time horizon (0=stable, 1=high risk)"
    )
    adverse_event_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability of adverse event (0-1)"
    )
    
    # Component Scores
    vital_signs_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text="Vital signs component score"
    )
    lifestyle_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text="Lifestyle factors component score"
    )
    medication_adherence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        default=0.0,
        help_text="Medication adherence score"
    )
    
    # Risk Factors Identified
    risk_factors = models.JSONField(
        default=list,
        help_text="List of identified risk factors contributing to score"
    )
    
    # Model Information
    model_version = models.CharField(max_length=20, default="1.0")
    calculation_method = models.CharField(max_length=50, default="rule_based")
    confidence_level = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model confidence in prediction (0-1)"
    )
    
    # Data Points Used
    data_points_used = models.JSONField(
        default=dict,
        help_text="Summary of data points used in calculation"
    )
    
    # Recommendations
    recommendations = models.JSONField(
        default=list,
        help_text="AI-generated recommendations to improve stability"
    )
    
    calculated_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this assessment expires")
    
    class Meta:
        db_table = 'vitals_risk_assessments'
        verbose_name = 'Risk Assessment'
        verbose_name_plural = 'Risk Assessments'
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - Risk: {self.risk_level} - Score: {self.stability_score}"
    
    @property
    def is_high_risk(self):
        """Check if this is a high risk assessment"""
        return self.risk_level in ['high', 'critical']
    
    @property
    def risk_percentage(self):
        """Get risk as percentage"""
        return round(self.adverse_event_probability * 100, 1)