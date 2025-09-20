"""
AI Engine models for VitalCircle's predictive analytics
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from patients.models import PatientProfile


class StabilityScore(models.Model):
    """AI-calculated stability scores and risk assessments"""
    RISK_LEVELS = [
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='stability_scores')
    
    # Core Score
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        help_text="Stability score (0-100, higher is better)"
    )
    risk_level = models.CharField(max_length=10, choices=RISK_LEVELS)
    
    # Component Scores
    vital_signs_score = models.FloatField(default=0.0, help_text="Vital signs component score")
    lifestyle_score = models.FloatField(default=0.0, help_text="Lifestyle factors component score")
    medication_adherence_score = models.FloatField(default=0.0, help_text="Medication adherence score")
    symptom_burden_score = models.FloatField(default=0.0, help_text="Symptom burden score")
    
    # Risk Factors
    identified_risks = models.JSONField(default=list, help_text="List of identified risk factors")
    risk_probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Probability of adverse event (0-1)"
    )
    
    # Model Information
    model_version = models.CharField(max_length=20, default="1.0")
    calculation_method = models.CharField(max_length=50, default="rule_based")
    confidence_level = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model confidence (0-1)"
    )
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now_add=True)
    data_freshness = models.DateTimeField(help_text="Timestamp of most recent data used")
    
    class Meta:
        db_table = 'ai_stability_scores'
        verbose_name = 'Stability Score'
        verbose_name_plural = 'Stability Scores'
        ordering = ['-calculated_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - Score: {self.score} ({self.risk_level})"


class HealthPrediction(models.Model):
    """AI predictions for future health events"""
    PREDICTION_TYPES = [
        ('blood_pressure_spike', 'Blood Pressure Spike'),
        ('medication_nonadherence', 'Medication Non-adherence'),
        ('symptom_flare', 'Symptom Flare-up'),
        ('emergency_risk', 'Emergency Risk'),
        ('hospitalization', 'Hospitalization Risk'),
        ('general_deterioration', 'General Health Deterioration'),
    ]
    
    TIME_HORIZONS = [
        ('24h', 'Next 24 Hours'),
        ('7d', 'Next 7 Days'),
        ('30d', 'Next 30 Days'),
        ('90d', 'Next 90 Days'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='health_predictions')
    
    prediction_type = models.CharField(max_length=30, choices=PREDICTION_TYPES)
    time_horizon = models.CharField(max_length=5, choices=TIME_HORIZONS)
    
    # Prediction Details
    probability = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Predicted probability (0-1)"
    )
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Model confidence (0-1)"
    )
    
    predicted_value = models.FloatField(null=True, blank=True, help_text="Predicted numerical value if applicable")
    description = models.TextField(help_text="Human-readable prediction description")
    
    # Contributing Factors
    key_factors = models.JSONField(default=list, help_text="Key factors influencing this prediction")
    data_points_used = models.JSONField(default=dict, help_text="Summary of data points used")
    
    # Model Information
    model_name = models.CharField(max_length=50)
    model_version = models.CharField(max_length=20)
    
    # Outcome Tracking
    actual_outcome = models.BooleanField(null=True, blank=True, help_text="Did the prediction come true?")
    outcome_recorded_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this prediction expires")
    
    class Meta:
        db_table = 'ai_health_predictions'
        verbose_name = 'Health Prediction'
        verbose_name_plural = 'Health Predictions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.get_prediction_type_display()} ({self.probability:.2%})"


class SmartNudge(models.Model):
    """AI-generated personalized health nudges and recommendations"""
    NUDGE_CATEGORIES = [
        ('medication', 'Medication Reminder'),
        ('lifestyle', 'Lifestyle Suggestion'),
        ('exercise', 'Exercise Recommendation'),
        ('diet', 'Dietary Advice'),
        ('stress', 'Stress Management'),
        ('sleep', 'Sleep Hygiene'),
        ('appointment', 'Appointment Reminder'),
        ('monitoring', 'Health Monitoring'),
        ('emergency', 'Emergency Alert'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low Priority'),
        ('medium', 'Medium Priority'),
        ('high', 'High Priority'),
        ('urgent', 'Urgent'),
    ]
    
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='smart_nudges')
    
    category = models.CharField(max_length=15, choices=NUDGE_CATEGORIES)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    
    # Content
    title = models.CharField(max_length=100)
    message = models.TextField()
    action_text = models.CharField(max_length=50, blank=True, help_text="Call-to-action button text")
    action_url = models.URLField(blank=True, help_text="URL for action button")
    
    # Personalization
    personalization_factors = models.JSONField(default=dict, help_text="Factors used for personalization")
    target_behavior = models.CharField(max_length=100, help_text="Target behavior to influence")
    
    # Delivery
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('dashboard', 'Dashboard'),
            ('email', 'Email'),
            ('sms', 'SMS'),
            ('push', 'Push Notification'),
            ('in_app', 'In-App Notification'),
        ],
        default='dashboard'
    )
    
    # Engagement Tracking
    delivered_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    dismissed_at = models.DateTimeField(null=True, blank=True)
    
    # Effectiveness
    user_feedback = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User feedback rating (1-5)"
    )
    outcome_achieved = models.BooleanField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(help_text="When this nudge expires")
    
    class Meta:
        db_table = 'ai_smart_nudges'
        verbose_name = 'Smart Nudge'
        verbose_name_plural = 'Smart Nudges'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.full_name} - {self.title} ({self.priority})"


class ModelPerformance(models.Model):
    """Track AI model performance and accuracy"""
    model_name = models.CharField(max_length=50)
    model_version = models.CharField(max_length=20)
    
    # Performance Metrics
    accuracy = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    precision = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    recall = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    f1_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    
    # Evaluation Details
    evaluation_period_start = models.DateTimeField()
    evaluation_period_end = models.DateTimeField()
    sample_size = models.IntegerField()
    
    # Model Metadata
    training_data_size = models.IntegerField()
    feature_count = models.IntegerField()
    deployment_date = models.DateTimeField()
    
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_model_performance'
        verbose_name = 'Model Performance'
        verbose_name_plural = 'Model Performance Records'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.model_name} v{self.model_version} - Accuracy: {self.accuracy:.2%}"