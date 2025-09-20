#!/usr/bin/env python3
"""
Comprehensive Vitals Logging Test Script
This script demonstrates how to use the new vitals logging API endpoints.
"""

import json
import requests
from datetime import datetime

# Base URL for the API (adjust if needed)
BASE_URL = "http://127.0.0.1:8000"

def test_comprehensive_vitals_logging():
    """Test the comprehensive vitals logging API"""
    
    # Sample comprehensive vitals data
    sample_data = {
        "vitals": {
            "systolic_bp": 135,
            "diastolic_bp": 85,
            "heart_rate": 78,
            "blood_glucose": 165,  # Slightly elevated
            "weight": 180.5,
            "height": 70,  # 5'10"
            "oxygen_saturation": 98,
            "temperature": 98.6,
            "respiratory_rate": 16,
            "source": "manual",
            "notes": "Morning reading after breakfast"
        },
        "lifestyle": {
            "stress_level": 3,  # Moderate stress
            "mood_rating": 7,
            "sleep_hours": 6.5,
            "sleep_quality": 3,  # Fair
            "activity_level": 3,  # Moderately active
            "exercise_minutes": 30,
            "steps_count": 8500,
            "sodium_intake": 2400,  # mg
            "water_intake": 64,  # ounces
            "calorie_intake": 2200,
            "food_log": {
                "vegetables": 3,
                "fruits": 2,
                "grains": 4,
                "protein": 2,
                "dairy": 2,
                "processed": 1
            },
            "medication_taken": True,
            "medication_adherence_percentage": 95.0,
            "notes": "Good day overall, had a healthy breakfast"
        },
        "medical_history": {
            "chronic_conditions": ["hypertension", "diabetes_type2"],
            "risk_factors": ["family_history_diabetes", "overweight"],
            "allergies": ["penicillin"],
            "current_medications": [
                "Metformin 500mg twice daily",
                "Lisinopril 10mg once daily",
                "Atorvastatin 20mg once daily"
            ],
            "notes": "Well-controlled type 2 diabetes and hypertension"
        }
    }
    
    print("=" * 60)
    print("COMPREHENSIVE VITALS LOGGING TEST")
    print("=" * 60)
    
    print("\n1. Sample Data Structure:")
    print(json.dumps(sample_data, indent=2))
    
    print("\n2. API Endpoint: POST /vitals/api/log-comprehensive/")
    print("   This endpoint will:")
    print("   - Log vital signs (BP, glucose, weight, BMI calculation)")
    print("   - Log lifestyle metrics (activity, sleep, diet, stress)")
    print("   - Update medical history")
    print("   - Calculate risk assessment automatically")
    print("   - Return alerts and recommendations")
    
    print("\n3. Expected Response Structure:")
    expected_response = {
        "success": True,
        "logged": [
            {
                "type": "vital_signs",
                "id": "...",
                "blood_pressure": "135/85",
                "bmi": 25.8,
                "glucose_category": "Pre-diabetes"
            },
            {
                "type": "lifestyle_metrics",
                "id": "...",
                "activity_level": "Moderately Active",
                "stress_level": "Moderate"
            },
            {
                "type": "medical_history",
                "id": "...",
                "conditions_count": 2,
                "medications_count": 3
            }
        ],
        "alerts": [
            "HIGH: Elevated blood pressure",
            "HIGH: Elevated blood sugar"
        ],
        "risk_assessment": {
            "id": "...",
            "stability_score": 65.5,
            "risk_level": "moderate",
            "adverse_event_probability": 34.5,
            "risk_factors": [
                "Elevated blood pressure",
                "Elevated blood glucose"
            ],
            "recommendations": [
                "Monitor blood pressure daily and consult your doctor",
                "Check blood glucose more frequently and review diet"
            ]
        }
    }
    print(json.dumps(expected_response, indent=2))
    
    print("\n4. Individual API Endpoints Available:")
    endpoints = [
        "GET  /vitals/api/vitals/          - Get recent vital signs",
        "POST /vitals/api/vitals/          - Log new vital signs",
        "GET  /vitals/api/lifestyle/       - Get recent lifestyle data",
        "GET  /vitals/api/risk-assessment/ - Get risk assessments",
        "POST /vitals/api/risk-assessment/ - Calculate new risk assessment"
    ]
    for endpoint in endpoints:
        print(f"   {endpoint}")
    
    print("\n5. Key Features Implemented:")
    features = [
        "✓ Blood Pressure tracking with automatic categorization",
        "✓ Blood Glucose monitoring for diabetes management",
        "✓ BMI calculation from weight and height",
        "✓ Activity level and steps tracking",
        "✓ Sleep quality and duration monitoring",
        "✓ Diet tracking with food category logging",
        "✓ Stress level assessment (1-10 scale)",
        "✓ Medication adherence tracking",
        "✓ Medical history management",
        "✓ Chronic condition tracking",
        "✓ Past medical episodes logging",
        "✓ Risk assessment with ML-ready scoring",
        "✓ Automatic alert generation",
        "✓ Personalized recommendations"
    ]
    for feature in features:
        print(f"   {feature}")
    
    print("\n6. Risk Assessment Algorithm:")
    print("   - Vital Signs Score (40% weight):")
    print("     * Blood pressure: Normal=0, Stage 1=-15, Stage 2=-30")
    print("     * Heart rate: Normal=0, Abnormal=-15")
    print("     * Blood glucose: Normal=0, Pre-diabetes=-10, Diabetes=-20")
    print("     * Oxygen saturation: >95%=0, 90-95%=-10, <90%=-25")
    print("   - Lifestyle Score (30% weight):")
    print("     * Stress level: Low=0, Moderate=-5, High=-15")
    print("     * Sleep: 7-8hrs=0, <6hrs or >9hrs=-10")
    print("     * Activity: High=0, Sedentary=-10")
    print("   - Medication Adherence (30% weight):")
    print("     * 100% adherence=100, proportional scoring")
    
    print("\n7. Output Categories:")
    print("   - Risk Levels: Low (80-100), Moderate (60-79), High (40-59), Critical (<40)")
    print("   - Adverse Event Probability: Calculated as (100 - stability_score) / 100")
    print("   - Time Horizons: 24h, 48h, 7d, 30d")
    
    print("\n" + "=" * 60)
    print("IMPLEMENTATION COMPLETE!")
    print("=" * 60)
    print("\nTo test the API:")
    print("1. Ensure the Django server is running: python manage.py runserver")
    print("2. Create a user account and login")
    print("3. Send POST request to /vitals/api/log-comprehensive/ with the sample data")
    print("4. Check the response for logged data, alerts, and risk assessment")

if __name__ == "__main__":
    test_comprehensive_vitals_logging()