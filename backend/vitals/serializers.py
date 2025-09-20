"""
Serializers for vitals app - Risk prediction and vitals validation
"""
from rest_framework import serializers


class RiskInputSerializer(serializers.Serializer):
    """
    Serializer for risk prediction input validation
    Validates patient vitals, lifestyle, and history data for ML risk assessment
    """
    
    # Required vitals
    systolic_bp = serializers.IntegerField(min_value=60, max_value=300, help_text="Systolic blood pressure (mmHg)")
    diastolic_bp = serializers.IntegerField(min_value=40, max_value=200, help_text="Diastolic blood pressure (mmHg)")
    heart_rate = serializers.IntegerField(min_value=30, max_value=250, help_text="Heart rate (BPM)")
    age = serializers.IntegerField(min_value=1, max_value=150, help_text="Patient age in years")
    
    # Optional vitals
    blood_glucose = serializers.FloatField(min_value=40, max_value=600, required=False, help_text="Blood glucose (mg/dL)")
    oxygen_saturation = serializers.FloatField(min_value=70, max_value=100, required=False, help_text="Oxygen saturation (%)")
    bmi = serializers.FloatField(min_value=10, max_value=60, required=False, help_text="Body Mass Index")
    
    # Optional lifestyle metrics
    daily_steps = serializers.IntegerField(min_value=0, max_value=100000, required=False, help_text="Daily steps count")
    sleep_hours = serializers.FloatField(min_value=0, max_value=24, required=False, help_text="Hours of sleep")
    sodium_intake_mg = serializers.IntegerField(min_value=0, max_value=10000, required=False, help_text="Sodium intake (mg)")
    calories = serializers.IntegerField(min_value=0, max_value=10000, required=False, help_text="Calorie intake")
    diet_category = serializers.ChoiceField(
        choices=[
            ('healthy', 'Healthy'),
            ('balanced', 'Balanced'),
            ('processed', 'Processed'),
            ('fast_food', 'Fast Food'),
            ('low_sodium', 'Low Sodium'),
            ('diabetic', 'Diabetic'),
            ('mediterranean', 'Mediterranean'),
            ('other', 'Other')
        ],
        required=False,
        help_text="Diet category"
    )
    stress_level = serializers.IntegerField(min_value=0, max_value=10, required=False, help_text="Stress level (0-10)")
    
    # Optional medical history
    chronic_conditions = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('hypertension', 'Hypertension'),
            ('diabetes_type1', 'Type 1 Diabetes'),
            ('diabetes_type2', 'Type 2 Diabetes'),
            ('heart_disease', 'Heart Disease'),
            ('stroke', 'Stroke'),
            ('kidney_disease', 'Kidney Disease'),
            ('copd', 'COPD'),
            ('asthma', 'Asthma'),
            ('depression', 'Depression'),
            ('anxiety', 'Anxiety'),
            ('other', 'Other')
        ]),
        required=False,
        help_text="List of chronic conditions"
    )
    
    past_episodes = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            ('hypertensive_crisis', 'Hypertensive Crisis'),
            ('hypoglycemia', 'Hypoglycemia'),
            ('hyperglycemia', 'Hyperglycemia'),
            ('heart_attack', 'Heart Attack'),
            ('stroke', 'Stroke'),
            ('emergency_room', 'Emergency Room Visit'),
            ('hospitalization', 'Hospitalization'),
            ('other', 'Other')
        ]),
        required=False,
        help_text="List of past medical episodes"
    )
    
    medication_adherence = serializers.FloatField(
        min_value=0, 
        max_value=100, 
        required=False, 
        help_text="Medication adherence percentage (0-100)"
    )
    
    def validate(self, data):
        """
        Custom validation for risk input data
        """
        # Validate blood pressure combination
        if data['systolic_bp'] <= data['diastolic_bp']:
            raise serializers.ValidationError("Systolic pressure must be higher than diastolic pressure")
        
        # Validate BMI if provided
        if 'bmi' in data and data['bmi'] < 15:
            raise serializers.ValidationError("BMI value seems too low, please verify")
        
        # Validate glucose for diabetes patients
        if 'chronic_conditions' in data and 'blood_glucose' not in data:
            diabetes_conditions = ['diabetes_type1', 'diabetes_type2']
            if any(condition in diabetes_conditions for condition in data['chronic_conditions']):
                # Warning but not error - glucose is helpful for diabetes patients
                pass
        
        return data


class RiskOutputSerializer(serializers.Serializer):
    """
    Serializer for risk prediction output validation
    Ensures consistent JSON schema for risk assessment responses
    """
    
    class RiskPredictionSerializer(serializers.Serializer):
        binary_risk_label = serializers.CharField(help_text="Risk label: 0 (stable) or 1 (high risk)")
        stability_score = serializers.CharField(help_text="Stability score: 0-100")
    
    class ExplainabilitySerializer(serializers.Serializer):
        key_factors = serializers.ListField(
            child=serializers.CharField(),
            help_text="List of key factors contributing to risk assessment"
        )
    
    risk_prediction = RiskPredictionSerializer()
    explainability = ExplainabilitySerializer()


class VitalsHistorySerializer(serializers.Serializer):
    """
    Serializer for historical vitals data to provide context for risk prediction
    """
    days = serializers.IntegerField(min_value=1, max_value=90, default=7, help_text="Number of days of history to include")
    include_trends = serializers.BooleanField(default=True, help_text="Include trend analysis")
    include_patterns = serializers.BooleanField(default=True, help_text="Include pattern recognition")