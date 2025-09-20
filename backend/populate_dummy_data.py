#!/usr/bin/env python
"""
Populate VitalCircle database with comprehensive dummy data
This script adds realistic dummy data to all models in the VitalCircle application
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
from django.utils import timezone
import random
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, PatientProfile as CorePatientProfile, VitalSigns as CoreVitalSigns, StabilityScore, HealthNudge, ClinicianNote
from patients.models import PatientProfile, HealthGoal, PatientNote
from clinicians.models import ClinicianProfile, PatientAssignment, ClinicalNote, TreatmentPlan
from vitals.models import VitalSigns, LifestyleMetrics, SymptomReport, MedicalHistory, RiskAssessment
from ai_engine.models import MedicineAlert, MedicineIntake, AIHealthNudge, WebLLMSession, StabilityScore as AIStabilityScore, HealthPrediction, SmartNudge, ModelPerformance


def clear_existing_data():
    """Clear existing dummy data (optional)"""
    print("🗑️ Clearing existing data...")
    
    # Clear in reverse dependency order
    models_to_clear = [
        # AI Engine models
        MedicineIntake, AIHealthNudge, WebLLMSession, HealthPrediction, SmartNudge, ModelPerformance,
        MedicineAlert, AIStabilityScore,
        
        # Vitals models
        RiskAssessment, SymptomReport, LifestyleMetrics, MedicalHistory, VitalSigns,
        
        # Clinician models
        TreatmentPlan, ClinicalNote, PatientAssignment, ClinicianProfile,
        
        # Patient models
        PatientNote, HealthGoal, PatientProfile,
        
        # Core models
        ClinicianNote, HealthNudge, StabilityScore, CoreVitalSigns, CorePatientProfile, UserProfile,
        
        # Users (except superusers)
    ]
    
    for model in models_to_clear:
        try:
            count = model.objects.count()
            model.objects.all().delete()
            print(f"  ✓ Cleared {count} records from {model.__name__}")
        except Exception as e:
            print(f"  ⚠️ Error clearing {model.__name__}: {e}")
    
    # Clear regular users (keep superusers)
    regular_users = User.objects.filter(is_superuser=False)
    count = regular_users.count()
    regular_users.delete()
    print(f"  ✓ Cleared {count} regular users")


def create_users_and_profiles():
    """Create users with different roles"""
    print("👥 Creating users and profiles...")
    
    users_data = [
        # Patients
        {
            'username': 'john_patient', 'email': 'john@example.com', 'first_name': 'John', 'last_name': 'Doe',
            'user_type': 'patient', 'dob': date(1990, 5, 15), 'gender': 'M', 'phone': '+1234567890'
        },
        {
            'username': 'sarah_patient', 'email': 'sarah@example.com', 'first_name': 'Sarah', 'last_name': 'Johnson',
            'user_type': 'patient', 'dob': date(1985, 8, 22), 'gender': 'F', 'phone': '+1234567891'
        },
        {
            'username': 'mike_patient', 'email': 'mike@example.com', 'first_name': 'Mike', 'last_name': 'Wilson',
            'user_type': 'patient', 'dob': date(1978, 12, 3), 'gender': 'M', 'phone': '+1234567892'
        },
        {
            'username': 'emma_patient', 'email': 'emma@example.com', 'first_name': 'Emma', 'last_name': 'Davis',
            'user_type': 'patient', 'dob': date(1992, 3, 10), 'gender': 'F', 'phone': '+1234567893'
        },
        
        # Clinicians
        {
            'username': 'dr_smith', 'email': 'dr.smith@hospital.com', 'first_name': 'Robert', 'last_name': 'Smith',
            'user_type': 'clinician', 'specialization': 'cardiology', 'license': 'LIC12345'
        },
        {
            'username': 'dr_garcia', 'email': 'dr.garcia@hospital.com', 'first_name': 'Maria', 'last_name': 'Garcia',
            'user_type': 'clinician', 'specialization': 'endocrinology', 'license': 'LIC12346'
        },
        {
            'username': 'nurse_brown', 'email': 'nurse.brown@hospital.com', 'first_name': 'Jennifer', 'last_name': 'Brown',
            'user_type': 'clinician', 'specialization': 'nursing', 'license': 'LIC12347'
        },
    ]
    
    created_users = {}
    
    for user_data in users_data:
        # Create Django User
        user = User.objects.create_user(
            username=user_data['username'],
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name'],
            password='password123'  # Default password for all demo users
        )
        
        # Create Core UserProfile
        core_profile = UserProfile.objects.create(
            user=user,
            user_type=user_data['user_type'],
            phone_number=user_data.get('phone', '')
        )
        
        # Create specific profiles based on user type
        if user_data['user_type'] == 'patient':
            # Create PatientProfile (for patients app)
            patient_profile = PatientProfile.objects.create(
                user=user,
                date_of_birth=user_data['dob'],
                gender=user_data['gender'],
                phone_number=user_data['phone'],
                emergency_contact='Emergency Contact Person',
                emergency_phone='+1987654321',
                chronic_conditions='Hypertension, Type 2 Diabetes',
                medications='Metformin 500mg, Lisinopril 10mg',
                allergies='Penicillin, Shellfish',
                current_stability_score=random.uniform(65, 95),
                risk_level=random.choice(['low', 'medium', 'high'])
            )
            created_users[user_data['username']] = {'user': user, 'profile': patient_profile, 'core_profile': core_profile}
            
        elif user_data['user_type'] == 'clinician':
            # Create ClinicianProfile
            clinician_profile = ClinicianProfile.objects.create(
                user=user,
                license_number=user_data['license'],
                specialization=user_data['specialization'],
                years_experience=random.randint(5, 25),
                phone='+1555000' + str(random.randint(100, 999)),
                hospital_affiliation='VitalCircle Medical Center',
                department=user_data['specialization'].title() + ' Department',
                medical_degree='MD',
                board_certifications=[user_data['specialization'].title() + ' Board Certification'],
                languages_spoken=['English', 'Spanish']
            )
            created_users[user_data['username']] = {'user': user, 'profile': clinician_profile, 'core_profile': core_profile}
    
    print(f"  ✓ Created {len(created_users)} users with profiles")
    return created_users


def create_vital_signs_data(users):
    """Create comprehensive vital signs data"""
    print("🩺 Creating vital signs data...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    for username, user_data in patient_users.items():
        patient_profile = user_data['profile']
        
        # Create multiple vital signs records over the past month
        for i in range(15):  # 15 records over past month
            days_ago = random.randint(0, 30)
            measured_time = timezone.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            
            # Generate realistic vital signs based on patient's condition
            base_systolic = random.randint(110, 140)
            base_diastolic = random.randint(70, 90)
            
            vital_signs = VitalSigns.objects.create(
                patient=patient_profile,
                systolic_bp=base_systolic + random.randint(-10, 15),
                diastolic_bp=base_diastolic + random.randint(-5, 10),
                heart_rate=random.randint(60, 100),
                temperature=round(random.uniform(97.5, 99.5), 1),
                weight=round(random.uniform(150, 200), 1),  # lbs
                height=random.randint(60, 75),  # inches
                blood_glucose=random.randint(80, 140),
                oxygen_saturation=random.randint(95, 100),
                respiratory_rate=random.randint(12, 20),
                measured_at=measured_time,
                source=random.choice(['manual', 'device', 'wearable']),
                notes=f"Routine measurement - feeling {random.choice(['good', 'tired', 'energetic', 'normal'])}"
            )
            
            # Create corresponding lifestyle metrics
            LifestyleMetrics.objects.create(
                patient=patient_profile,
                stress_level=random.randint(1, 5),
                mood_rating=random.randint(4, 9),
                sleep_hours=round(random.uniform(6, 9), 1),
                sleep_quality=random.randint(2, 5),
                sodium_intake=random.uniform(1500, 3000),
                water_intake=random.uniform(40, 80),
                calorie_intake=random.randint(1800, 2500),
                food_log={
                    'vegetables': random.randint(2, 6),
                    'fruits': random.randint(1, 4),
                    'protein': random.randint(2, 4),
                    'grains': random.randint(3, 8)
                },
                activity_level=random.randint(2, 5),
                exercise_minutes=random.randint(0, 90),
                steps_count=random.randint(3000, 12000),
                medication_taken=random.choice([True, True, True, False]),  # 75% adherence
                recorded_at=measured_time
            )
    
    print(f"  ✓ Created vital signs for {len(patient_users)} patients")


def create_medical_history_data(users):
    """Create medical history for patients"""
    print("📋 Creating medical history data...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    for username, user_data in patient_users.items():
        patient_profile = user_data['profile']
        
        MedicalHistory.objects.create(
            patient=patient_profile,
            chronic_conditions=['hypertension', 'diabetes_type2'] if random.choice([True, False]) else ['hypertension'],
            past_episodes=[
                {
                    'type': 'emergency_room',
                    'date': '2024-06-15',
                    'description': 'Chest pain, ruled out heart attack',
                    'severity': 'moderate'
                },
                {
                    'type': 'hyperglycemia',
                    'date': '2024-03-22',
                    'description': 'Blood sugar spike after holiday meal',
                    'severity': 'mild'
                }
            ],
            family_history={
                'diabetes': 'Father, Grandfather',
                'heart_disease': 'Mother',
                'hypertension': 'Both parents'
            },
            risk_factors=['sedentary_lifestyle', 'family_history'],
            allergies=[
                {'allergen': 'Penicillin', 'reaction': 'Rash'},
                {'allergen': 'Shellfish', 'reaction': 'Swelling'}
            ],
            current_medications=[
                {'name': 'Metformin', 'dosage': '500mg', 'frequency': 'twice daily'},
                {'name': 'Lisinopril', 'dosage': '10mg', 'frequency': 'once daily'},
                {'name': 'Vitamin D3', 'dosage': '1000 IU', 'frequency': 'once daily'}
            ],
            notes='Patient is generally compliant with medications. Needs encouragement for lifestyle changes.'
        )
    
    print(f"  ✓ Created medical history for {len(patient_users)} patients")


def create_medicine_alerts_data(users):
    """Create medicine alerts and intake records"""
    print("💊 Creating medicine alerts and intake data...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    for username, user_data in patient_users.items():
        user = user_data['user']
        
        # Create medicine alerts
        medicines = [
            {'name': 'Metformin', 'dosage': '500mg', 'times': ['08:00', '20:00']},
            {'name': 'Lisinopril', 'dosage': '10mg', 'times': ['08:00']},
            {'name': 'Vitamin D3', 'dosage': '1000 IU', 'times': ['08:00']},
            {'name': 'Omega-3', 'dosage': '1000mg', 'times': ['19:00']}
        ]
        
        for med in medicines:
            alert = MedicineAlert.objects.create(
                patient=user,
                medicine_name=med['name'],
                dosage=med['dosage'],
                times_per_day=len(med['times']),
                alert_times=med['times'],
                start_date=date.today() - timedelta(days=30),
                end_date=date.today() + timedelta(days=60),
                priority=random.choice(['medium', 'high']),
                enable_ai_nudges=True,
                ai_context={'condition': 'diabetes_management', 'importance': 'high'}
            )
            
            # Create intake records for past week
            for i in range(7):
                for time_str in med['times']:
                    scheduled_time = timezone.now() - timedelta(days=i) + timedelta(
                        hours=int(time_str.split(':')[0]),
                        minutes=int(time_str.split(':')[1])
                    )
                    
                    MedicineIntake.objects.create(
                        alert=alert,
                        patient=user,
                        scheduled_time=scheduled_time,
                        actual_time=scheduled_time + timedelta(minutes=random.randint(-30, 60)),
                        status=random.choice(['taken', 'taken', 'taken', 'late', 'missed']),  # Mostly taken
                        notes=random.choice(['', 'Felt fine', 'Slight nausea', 'Good day']),
                        mood_before=random.randint(3, 5),
                        mood_after=random.randint(3, 5)
                    )
    
    print(f"  ✓ Created medicine alerts for {len(patient_users)} patients")


def create_ai_health_nudges(users):
    """Create AI-generated health nudges"""
    print("🤖 Creating AI health nudges...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    nudge_templates = [
        {
            'type': 'medicine_reminder',
            'title': 'Time for your evening medication!',
            'message': 'Hi {name}! Don\'t forget to take your Metformin. Consistent medication helps maintain stable blood sugar levels.',
            'action': 'Mark as Taken'
        },
        {
            'type': 'lifestyle_suggestion',
            'title': 'Great job on your morning walk!',
            'message': 'Your activity level is improving! Try adding 5 more minutes to your evening routine.',
            'action': 'View Exercise Plan'
        },
        {
            'type': 'educational',
            'title': 'Understanding Your Blood Pressure',
            'message': 'Your recent reading of 125/82 is in the elevated range. Here are some tips to help lower it naturally.',
            'action': 'Learn More'
        }
    ]
    
    for username, user_data in patient_users.items():
        user = user_data['user']
        
        for i in range(5):  # 5 nudges per patient
            template = random.choice(nudge_templates)
            
            AIHealthNudge.objects.create(
                patient=user,
                nudge_type=template['type'],
                title=template['title'],
                message=template['message'].format(name=user.first_name),
                action_suggestion=template['action'],
                model_used='WebLLM-Llama-3.2-1B',
                prompt_context={
                    'patient_condition': 'diabetes_hypertension',
                    'recent_vitals': {'bp': '125/82', 'glucose': '145'},
                    'medication_adherence': '85%'
                },
                generation_tokens=random.randint(50, 150),
                generation_time_ms=random.randint(800, 2000),
                scheduled_for=timezone.now() + timedelta(hours=random.randint(1, 48)),
                expires_at=timezone.now() + timedelta(days=3),
                status=random.choice(['generated', 'delivered', 'viewed'])
            )
    
    print(f"  ✓ Created AI health nudges for {len(patient_users)} patients")


def create_risk_assessments(users):
    """Create risk assessments and stability scores"""
    print("⚠️ Creating risk assessments...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    for username, user_data in patient_users.items():
        patient_profile = user_data['profile']
        
        # Create multiple risk assessments over time
        for i in range(3):
            days_ago = i * 7  # Weekly assessments
            assessment_time = timezone.now() - timedelta(days=days_ago)
            
            stability_score = random.uniform(60, 95)
            risk_level = 'low' if stability_score > 80 else 'medium' if stability_score > 65 else 'high'
            
            RiskAssessment.objects.create(
                patient=patient_profile,
                assessment_type='automated',
                stability_score=stability_score,
                risk_level=risk_level,
                time_horizon='48h',
                adverse_event_risk=stability_score < 70,
                adverse_event_probability=max(0, (100 - stability_score) / 100),
                vital_signs_score=random.uniform(70, 95),
                lifestyle_score=random.uniform(60, 85),
                medication_adherence_score=random.uniform(75, 95),
                risk_factors=[
                    'elevated_blood_pressure',
                    'irregular_medication_timing',
                    'high_stress_levels'
                ] if risk_level == 'high' else ['minor_lifestyle_factors'],
                recommendations=[
                    'Monitor blood pressure twice daily',
                    'Maintain consistent medication schedule',
                    'Reduce sodium intake to <2000mg daily',
                    'Increase physical activity to 150 minutes/week'
                ],
                calculated_at=assessment_time,
                expires_at=assessment_time + timedelta(days=7),
                confidence_level=random.uniform(0.8, 0.95),
                data_points_used={
                    'vital_signs_count': 10,
                    'lifestyle_entries': 7,
                    'medication_records': 14
                }
            )
    
    print(f"  ✓ Created risk assessments for {len(patient_users)} patients")


def create_health_goals_and_notes(users):
    """Create health goals and patient notes"""
    print("🎯 Creating health goals and notes...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    for username, user_data in patient_users.items():
        patient_profile = user_data['profile']
        user = user_data['user']
        
        # Create health goals
        goals = [
            {
                'type': 'blood_pressure',
                'title': 'Lower Blood Pressure',
                'description': 'Maintain systolic BP below 130 mmHg',
                'target': 130,
                'current': random.uniform(125, 140),
                'unit': 'mmHg'
            },
            {
                'type': 'weight',
                'title': 'Weight Management',
                'description': 'Lose 10 pounds in 3 months',
                'target': 180,
                'current': random.uniform(185, 195),
                'unit': 'lbs'
            },
            {
                'type': 'exercise',
                'title': 'Daily Exercise',
                'description': 'Walk at least 8000 steps daily',
                'target': 8000,
                'current': random.uniform(5000, 7500),
                'unit': 'steps'
            }
        ]
        
        for goal_data in goals:
            goal = HealthGoal.objects.create(
                patient=patient_profile,
                goal_type=goal_data['type'],
                title=goal_data['title'],
                description=goal_data['description'],
                target_value=goal_data['target'],
                current_value=goal_data['current'],
                unit=goal_data['unit'],
                target_date=date.today() + timedelta(days=90),
                status='active'
            )
            goal.calculate_progress()
            goal.save()
        
        # Create patient notes
        note_templates = [
            'Feeling much better after starting the new medication routine',
            'Had some difficulty sleeping last night, stress levels elevated',
            'Great workout today! Managed to walk for 45 minutes',
            'Blood sugar levels seem more stable this week',
            'Forgot to take evening medication yesterday'
        ]
        
        for i in range(3):
            PatientNote.objects.create(
                patient=patient_profile,
                note_type=random.choice(['general', 'symptom', 'medication']),
                title=f'Daily Log - {(timezone.now() - timedelta(days=i)).strftime("%Y-%m-%d")}',
                content=random.choice(note_templates),
                created_by=user,
                tags=['daily_log', 'self_reported']
            )
    
    print(f"  ✓ Created health goals and notes for {len(patient_users)} patients")


def create_clinician_data(users):
    """Create clinician-related data"""
    print("🏥 Creating clinician data...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    clinician_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'clinician'}
    
    if not clinician_users:
        print("  ⚠️ No clinicians found, skipping clinician data creation")
        return
    
    # Assign patients to clinicians
    for username, patient_data in patient_users.items():
        clinician_username = random.choice(list(clinician_users.keys()))
        clinician_data = clinician_users[clinician_username]
        
        PatientAssignment.objects.create(
            clinician=clinician_data['profile'],
            patient=patient_data['profile'],
            assignment_type=random.choice(['primary', 'specialist']),
            status='active',
            notes=f'Assigned for ongoing {clinician_data["profile"].specialization} care'
        )
        
        # Create clinical notes
        ClinicalNote.objects.create(
            clinician=clinician_data['profile'],
            patient=patient_data['profile'],
            note_type='assessment',
            title='Initial Assessment',
            content=f'Patient {patient_data["user"].get_full_name()} presents with well-controlled diabetes and hypertension. Medication adherence is good. Recommend continued monitoring and lifestyle modifications.',
            diagnosis_codes=['E11.9', 'I10'],  # Type 2 diabetes, Essential hypertension
            medications_prescribed=[
                {'name': 'Metformin', 'dosage': '500mg BID'},
                {'name': 'Lisinopril', 'dosage': '10mg QD'}
            ],
            recommendations='Continue current medications, monitor BP at home, follow up in 3 months',
            follow_up_required=True,
            follow_up_date=timezone.now() + timedelta(days=90)
        )
        
        # Create treatment plan
        TreatmentPlan.objects.create(
            clinician=clinician_data['profile'],
            patient=patient_data['profile'],
            title='Diabetes and Hypertension Management',
            description='Comprehensive care plan for managing Type 2 diabetes and essential hypertension',
            status='active',
            priority='medium',
            goals=[
                'Maintain HbA1c < 7%',
                'Keep BP < 130/80 mmHg',
                'Weight reduction of 5-10%',
                'Improve medication adherence to >90%'
            ],
            interventions=[
                'Daily home BP monitoring',
                'Monthly weight checks',
                'Quarterly HbA1c testing',
                'Annual eye exam'
            ],
            medications=[
                'Metformin 500mg twice daily',
                'Lisinopril 10mg once daily',
                'Vitamin D3 1000 IU daily'
            ],
            lifestyle_modifications=[
                'Reduce sodium intake to <2000mg/day',
                'Exercise 150 minutes/week',
                'Monitor carbohydrate intake',
                'Stress management techniques'
            ],
            start_date=timezone.now(),
            review_date=timezone.now() + timedelta(days=90),
            adherence_score=random.randint(75, 95)
        )
    
    print(f"  ✓ Created clinician data for {len(patient_users)} assignments")


def create_ai_predictions_and_analytics(users):
    """Create AI predictions and model performance data"""
    print("📊 Creating AI predictions and analytics...")
    
    patient_users = {k: v for k, v in users.items() if v['core_profile'].user_type == 'patient'}
    
    # Create health predictions
    for username, user_data in patient_users.items():
        patient_profile = user_data['profile']
        
        predictions = [
            {
                'type': 'blood_pressure_spike',
                'horizon': '24h',
                'probability': random.uniform(0.1, 0.3),
                'description': 'Low risk of blood pressure spike in next 24 hours'
            },
            {
                'type': 'medication_nonadherence',
                'horizon': '7d',
                'probability': random.uniform(0.15, 0.35),
                'description': 'Moderate risk of missing medications this week'
            },
            {
                'type': 'emergency_risk',
                'horizon': '30d',
                'probability': random.uniform(0.05, 0.15),
                'description': 'Low risk of emergency event in next month'
            }
        ]
        
        for pred in predictions:
            HealthPrediction.objects.create(
                patient=patient_profile,
                prediction_type=pred['type'],
                time_horizon=pred['horizon'],
                probability=pred['probability'],
                confidence=random.uniform(0.75, 0.95),
                description=pred['description'],
                key_factors=[
                    'recent_bp_trends',
                    'medication_timing_variance',
                    'stress_level_increases'
                ],
                data_points_used={
                    'vital_signs': 15,
                    'lifestyle_metrics': 10,
                    'medication_records': 20
                },
                model_name='VitalCircle-Risk-Predictor',
                model_version='2.1',
                expires_at=timezone.now() + timedelta(days=7)
            )
    
    # Create model performance records
    ModelPerformance.objects.create(
        model_name='VitalCircle-Risk-Predictor',
        model_version='2.1',
        accuracy=0.87,
        precision=0.84,
        recall=0.89,
        f1_score=0.86,
        evaluation_period_start=timezone.now() - timedelta(days=30),
        evaluation_period_end=timezone.now(),
        sample_size=1000,
        training_data_size=5000,
        feature_count=25,
        deployment_date=timezone.now() - timedelta(days=60),
        notes='Excellent performance on diabetes and hypertension risk prediction'
    )
    
    ModelPerformance.objects.create(
        model_name='WebLLM-Nudge-Generator',
        model_version='1.3',
        accuracy=0.92,
        precision=0.90,
        recall=0.94,
        f1_score=0.92,
        evaluation_period_start=timezone.now() - timedelta(days=30),
        evaluation_period_end=timezone.now(),
        sample_size=500,
        training_data_size=2000,
        feature_count=15,
        deployment_date=timezone.now() - timedelta(days=45),
        notes='High user engagement with AI-generated health nudges'
    )
    
    print(f"  ✓ Created AI predictions for {len(patient_users)} patients")


def print_database_summary():
    """Print summary of created data"""
    print("\n📈 Database Summary:")
    print("=" * 50)
    
    models_to_check = [
        (User, 'Users'),
        (UserProfile, 'User Profiles'),
        (PatientProfile, 'Patient Profiles'),
        (ClinicianProfile, 'Clinician Profiles'),
        (VitalSigns, 'Vital Signs Records'),
        (LifestyleMetrics, 'Lifestyle Metrics'),
        (MedicalHistory, 'Medical Histories'),
        (RiskAssessment, 'Risk Assessments'),
        (MedicineAlert, 'Medicine Alerts'),
        (MedicineIntake, 'Medicine Intake Records'),
        (AIHealthNudge, 'AI Health Nudges'),
        (HealthGoal, 'Health Goals'),
        (PatientNote, 'Patient Notes'),
        (PatientAssignment, 'Patient Assignments'),
        (ClinicalNote, 'Clinical Notes'),
        (TreatmentPlan, 'Treatment Plans'),
        (HealthPrediction, 'Health Predictions'),
        (ModelPerformance, 'Model Performance Records'),
    ]
    
    for model, name in models_to_check:
        count = model.objects.count()
        print(f"  {name}: {count}")
    
    print("=" * 50)
    print("✅ Database populated successfully!")
    print("\n📝 Login Information:")
    print("Default password for all demo users: password123")
    print("\nDemo Users Created:")
    print("  Patients: john_patient, sarah_patient, mike_patient, emma_patient")
    print("  Clinicians: dr_smith, dr_garcia, nurse_brown")


def main():
    """Main function to populate the database"""
    print("🚀 Starting VitalCircle Database Population")
    print("=" * 50)
    
    try:
        # Optional: Clear existing data (uncomment if needed)
        # clear_existing_data()
        
        # Create data in proper order (respecting foreign key dependencies)
        users = create_users_and_profiles()
        create_vital_signs_data(users)
        create_medical_history_data(users)
        create_medicine_alerts_data(users)
        create_ai_health_nudges(users)
        create_risk_assessments(users)
        create_health_goals_and_notes(users)
        create_clinician_data(users)
        create_ai_predictions_and_analytics(users)
        
        print_database_summary()
        
    except Exception as e:
        print(f"❌ Error during database population: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()