"""
AI Engine models for VitalCircle's predictive analytics
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from patients.models import PatientProfile


class MedicineAlert(models.Model):
    """Medicine intake alerts and scheduling"""
    ALERT_TYPES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('as_needed', 'As Needed'),
        ('custom', 'Custom Schedule'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicine_alerts')
    
    # Medicine Details
    medicine_name = models.CharField(max_length=100)
    dosage = models.CharField(max_length=50, help_text="e.g., '10mg', '2 tablets'")
    form = models.CharField(max_length=30, default='tablet', help_text="tablet, capsule, liquid, injection, etc.")
    instructions = models.TextField(blank=True, help_text="Special instructions for taking the medicine")
    
    # Scheduling
    alert_type = models.CharField(max_length=15, choices=ALERT_TYPES, default='daily')
    times_per_day = models.IntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(10)])
    alert_times = models.JSONField(
        default=list, 
        help_text="List of times in HH:MM format, e.g., ['08:00', '14:00', '20:00']"
    )
    
    # Custom scheduling for complex schedules
    custom_schedule = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom schedule configuration for complex patterns"
    )
    
    # Alert Settings
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    reminder_before_minutes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(120)],
        help_text="Minutes before scheduled time to send reminder"
    )
    snooze_duration = models.IntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Snooze duration in minutes"
    )
    
    # Duration
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, help_text="Leave blank for ongoing medication")
    
    # Status
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')
    is_enabled = models.BooleanField(default=True)
    
    # WebLLM Integration
    enable_ai_nudges = models.BooleanField(
        default=True, 
        help_text="Enable AI-generated contextual nudges for this medication"
    )
    ai_context = models.JSONField(
        default=dict,
        blank=True,
        help_text="Context data for AI nudge generation"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_medicine_alerts'
    )
    
    class Meta:
        db_table = 'ai_medicine_alerts'
        verbose_name = 'Medicine Alert'
        verbose_name_plural = 'Medicine Alerts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.username} - {self.medicine_name} ({self.alert_type})"


class MedicineIntake(models.Model):
    """Track actual medicine intake events"""
    INTAKE_STATUS = [
        ('taken', 'Taken'),
        ('missed', 'Missed'),
        ('partial', 'Partial'),
        ('late', 'Late'),
        ('skipped', 'Intentionally Skipped'),
    ]
    
    alert = models.ForeignKey(MedicineAlert, on_delete=models.CASCADE, related_name='intake_records')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medicine_intakes')
    
    # Scheduled vs Actual
    scheduled_time = models.DateTimeField(help_text="When the medicine was scheduled to be taken")
    actual_time = models.DateTimeField(null=True, blank=True, help_text="When the medicine was actually taken")
    
    # Status
    status = models.CharField(max_length=15, choices=INTAKE_STATUS)
    dosage_taken = models.CharField(
        max_length=50, 
        blank=True, 
        help_text="Actual dosage taken if different from scheduled"
    )
    
    # Context
    notes = models.TextField(blank=True, help_text="Patient notes about this intake")
    side_effects = models.TextField(blank=True, help_text="Any side effects experienced")
    mood_before = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Mood rating before taking medicine (1-5)"
    )
    mood_after = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Mood rating after taking medicine (1-5)"
    )
    
    # WebLLM Context
    ai_nudge_used = models.BooleanField(default=False, help_text="Was an AI nudge involved in this intake?")
    nudge_effectiveness = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How effective was the AI nudge? (1-5)"
    )
    
    # Metadata
    recorded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_medicine_intakes'
        verbose_name = 'Medicine Intake'
        verbose_name_plural = 'Medicine Intakes'
        ordering = ['-scheduled_time']
    
    def __str__(self):
        return f"{self.patient.username} - {self.alert.medicine_name} - {self.status}"


class AIHealthNudge(models.Model):
    """AI-generated contextual health nudges using WebLLM"""
    NUDGE_TYPES = [
        ('medicine_reminder', 'Medicine Reminder'),
        ('adherence_encouragement', 'Adherence Encouragement'),
        ('side_effect_guidance', 'Side Effect Guidance'),
        ('lifestyle_suggestion', 'Lifestyle Suggestion'),
        ('motivation', 'Motivational Message'),
        ('educational', 'Educational Content'),
        ('appointment_reminder', 'Appointment Reminder'),
    ]
    
    STATUS_CHOICES = [
        ('generated', 'Generated'),
        ('delivered', 'Delivered'),
        ('viewed', 'Viewed'),
        ('acted_upon', 'Acted Upon'),
        ('dismissed', 'Dismissed'),
        ('expired', 'Expired'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_nudges')
    medicine_alert = models.ForeignKey(
        MedicineAlert, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='ai_nudges'
    )
    
    # Nudge Content
    nudge_type = models.CharField(max_length=25, choices=NUDGE_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField(help_text="AI-generated personalized message")
    action_suggestion = models.CharField(max_length=200, blank=True)
    
    # AI Generation Context
    model_used = models.CharField(max_length=50, default='WebLLM-Local')
    prompt_context = models.JSONField(
        default=dict,
        help_text="Context data used to generate the nudge"
    )
    generation_tokens = models.IntegerField(default=0, help_text="Number of tokens generated")
    generation_time_ms = models.IntegerField(default=0, help_text="Time taken to generate (ms)")
    
    # Personalization Factors
    patient_history = models.JSONField(
        default=dict,
        help_text="Patient history factors considered"
    )
    current_context = models.JSONField(
        default=dict,
        help_text="Current situational context"
    )
    behavioral_patterns = models.JSONField(
        default=dict,
        help_text="Patient behavioral patterns identified"
    )
    
    # Delivery and Engagement
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='generated')
    delivery_method = models.CharField(
        max_length=20,
        choices=[
            ('dashboard_toast', 'Dashboard Toast'),
            ('dashboard_card', 'Dashboard Card'),
            ('modal', 'Modal Dialog'),
            ('notification', 'Browser Notification'),
            ('email', 'Email'),
        ],
        default='dashboard_toast'
    )
    
    # Timing
    scheduled_for = models.DateTimeField(help_text="When to deliver this nudge")
    delivered_at = models.DateTimeField(null=True, blank=True)
    viewed_at = models.DateTimeField(null=True, blank=True)
    acted_upon_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(help_text="When this nudge expires")
    
    # Effectiveness Tracking
    user_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User rating of nudge helpfulness (1-5)"
    )
    led_to_action = models.BooleanField(default=False)
    action_type = models.CharField(max_length=50, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_health_nudges'
        verbose_name = 'AI Health Nudge'
        verbose_name_plural = 'AI Health Nudges'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.patient.username} - {self.nudge_type} - {self.title[:30]}"


class WebLLMSession(models.Model):
    """Track WebLLM usage sessions for analytics"""
    SESSION_TYPES = [
        ('medicine_consultation', 'Medicine Consultation'),
        ('nudge_generation', 'Nudge Generation'),
        ('health_education', 'Health Education'),
        ('symptom_analysis', 'Symptom Analysis'),
        ('general_chat', 'General Health Chat'),
    ]
    
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webllm_sessions')
    session_type = models.CharField(max_length=25, choices=SESSION_TYPES)
    
    # Model Information
    model_id = models.CharField(max_length=100, help_text="WebLLM model identifier used")
    model_size = models.CharField(max_length=20, help_text="Model size (e.g., '1B', '3B')")
    
    # Session Details
    session_start = models.DateTimeField(auto_now_add=True)
    session_end = models.DateTimeField(null=True, blank=True)
    total_messages = models.IntegerField(default=0)
    total_tokens_generated = models.IntegerField(default=0)
    
    # Performance Metrics
    average_response_time_ms = models.IntegerField(default=0)
    total_generation_time_ms = models.IntegerField(default=0)
    
    # Context
    initial_prompt = models.TextField(blank=True)
    conversation_summary = models.TextField(blank=True)
    
    # User Satisfaction
    user_rating = models.IntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="User rating of session helpfulness (1-5)"
    )
    feedback = models.TextField(blank=True)
    
    # Technical Details
    browser_info = models.JSONField(default=dict)
    device_info = models.JSONField(default=dict)
    performance_stats = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'ai_webllm_sessions'
        verbose_name = 'WebLLM Session'
        verbose_name_plural = 'WebLLM Sessions'
        ordering = ['-session_start']
    
    def __str__(self):
        return f"{self.patient.username} - {self.session_type} - {self.session_start}"


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