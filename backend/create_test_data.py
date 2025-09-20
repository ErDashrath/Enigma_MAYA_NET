"""
Test data creation script for VitalCircle
Run this with: python manage.py shell < create_test_data.py
"""

import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth.models import User

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')
django.setup()

from patients.models import PatientProfile, HealthGoal, PatientNote
from vitals.models import VitalSigns, LifestyleMetrics, SymptomReport
from ai_engine.models import StabilityScore, HealthPrediction, SmartNudge
from clinicians.models import ClinicianProfile, PatientAssignment, ClinicalNote, TreatmentPlan

def create_test_data():
    print("Creating test data for VitalCircle...")
    
    # Create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@vitalcircle.com',
            'first_name': 'Admin',
            'last_name': 'User',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✓ Created admin user: {admin_user.username}")
    else:
        print(f"✓ Admin user already exists: {admin_user.username}")
    
    # Create test patient
    patient_user, created = User.objects.get_or_create(
        username='john_doe',
        defaults={
            'email': 'john.doe@email.com',
            'first_name': 'John',
            'last_name': 'Doe',
        }
    )
    if created:
        patient_user.set_password('patient123')
        patient_user.save()
        print(f"✓ Created patient user: {patient_user.username}")
    
    # Create patient profile
    patient_profile, created = PatientProfile.objects.get_or_create(
        user=patient_user,
        defaults={
            'date_of_birth': datetime(1980, 5, 15).date(),
            'gender': 'male',
            'phone': '+1-555-0123',
            'emergency_contact_name': 'Jane Doe',
            'emergency_contact_phone': '+1-555-0124',
            'chronic_conditions': ['hypertension', 'diabetes_type2'],
            'allergies': ['penicillin'],
            'current_medications': ['lisinopril', 'metformin'],
            'insurance_provider': 'HealthCare Plus',
            'insurance_id': 'HC123456789',
        }
    )
    if created:
        print(f"✓ Created patient profile: {patient_profile.full_name}")
    
    # Create test clinician
    clinician_user, created = User.objects.get_or_create(
        username='dr_smith',
        defaults={
            'email': 'dr.smith@hospital.com',
            'first_name': 'Sarah',
            'last_name': 'Smith',
        }
    )
    if created:
        clinician_user.set_password('doctor123')
        clinician_user.save()
        print(f"✓ Created clinician user: {clinician_user.username}")
    
    # Create clinician profile
    clinician_profile, created = ClinicianProfile.objects.get_or_create(
        user=clinician_user,
        defaults={
            'license_number': 'MD123456',
            'specialization': 'cardiology',
            'years_experience': 12,
            'phone': '+1-555-0200',
            'hospital_affiliation': 'General Hospital',
            'department': 'Cardiology',
            'medical_degree': 'MD from Harvard Medical School',
            'board_certifications': ['Cardiology', 'Internal Medicine'],
            'languages_spoken': ['English', 'Spanish'],
        }
    )
    if created:
        print(f"✓ Created clinician profile: Dr. {clinician_profile.user.get_full_name()}")
    
    # Create patient assignment
    assignment, created = PatientAssignment.objects.get_or_create(
        clinician=clinician_profile,
        patient=patient_profile,
        assignment_type='primary',
        defaults={
            'status': 'active',
            'notes': 'Primary care assignment for chronic condition management'
        }
    )
    if created:
        print(f"✓ Created patient assignment: {assignment}")
    
    # Create sample vital signs (last 7 days)
    for i in range(7):
        date = timezone.now() - timedelta(days=i)
        vital_signs, created = VitalSigns.objects.get_or_create(
            patient=patient_profile,
            recorded_at=date,
            defaults={
                'systolic_bp': 135 + (i * 2),  # Slightly elevated, trending up
                'diastolic_bp': 85 + i,
                'heart_rate': 75 + (i % 3),
                'temperature': 98.6,
                'respiratory_rate': 16,
                'oxygen_saturation': 98,
                'blood_glucose': 145 + (i * 5),  # Slightly elevated
                'weight': 180.5,
                'notes': f'Day {7-i} vitals - routine check'
            }
        )
        if created:
            print(f"✓ Created vital signs for day {7-i}")
    
    # Create lifestyle metrics
    for i in range(5):
        date = timezone.now() - timedelta(days=i)
        lifestyle, created = LifestyleMetrics.objects.get_or_create(
            patient=patient_profile,
            recorded_at=date,
            defaults={
                'stress_level': 3 + (i % 2),  # Moderate stress
                'sleep_hours': 6.5 + (i * 0.2),
                'sleep_quality': 3,
                'exercise_minutes': 20 + (i * 5),
                'exercise_intensity': 'moderate',
                'diet_quality': 3,
                'water_intake': 6 + i,
                'medication_adherence': 85 - (i * 2),  # Declining adherence
                'mood_rating': 3,
                'notes': f'Lifestyle tracking day {5-i}'
            }
        )
        if created:
            print(f"✓ Created lifestyle metrics for day {5-i}")
    
    # Create health goals
    goals_data = [
        {
            'goal_type': 'blood_pressure_control',
            'title': 'Reduce Blood Pressure',
            'description': 'Maintain systolic BP below 130 mmHg',
            'target_value': 130,
            'current_value': 135,
            'baseline_value': 145,
            'measurement_unit': 'mmHg',
            'target_date': (timezone.now() + timedelta(days=90)).date(),
        },
        {
            'goal_type': 'weight_loss',
            'title': 'Lose Weight',
            'description': 'Reduce weight to improve overall health',
            'target_value': 170,
            'current_value': 180.5,
            'baseline_value': 185,
            'measurement_unit': 'lbs',
            'target_date': (timezone.now() + timedelta(days=180)).date(),
        }
    ]
    
    for goal_data in goals_data:
        goal, created = HealthGoal.objects.get_or_create(
            patient=patient_profile,
            goal_type=goal_data['goal_type'],
            defaults=goal_data
        )
        if created:
            print(f"✓ Created health goal: {goal.title}")
    
    # Create symptom reports
    symptoms_data = [
        {
            'symptoms': ['headache', 'fatigue'],
            'severity_level': 2,
            'duration_hours': 4,
            'triggers': ['stress', 'lack_of_sleep'],
            'relief_methods': ['rest', 'hydration'],
            'additional_notes': 'Mild symptoms, manageable'
        },
        {
            'symptoms': ['chest_tightness'],
            'severity_level': 3,
            'duration_hours': 1,
            'triggers': ['physical_exertion'],
            'relief_methods': ['rest'],
            'additional_notes': 'Occurred during exercise'
        }
    ]
    
    for i, symptom_data in enumerate(symptoms_data):
        report_date = timezone.now() - timedelta(days=i+1)
        symptom_data['reported_at'] = report_date
        symptom_report, created = SymptomReport.objects.get_or_create(
            patient=patient_profile,
            reported_at=report_date,
            defaults=symptom_data
        )
        if created:
            print(f"✓ Created symptom report: {', '.join(symptom_report.symptoms)}")
    
    # Create clinical notes
    notes_data = [
        {
            'note_type': 'assessment',
            'title': 'Initial Assessment',
            'content': 'Patient presents with well-controlled hypertension and type 2 diabetes. Current medications are effective but need monitoring for adherence.',
            'diagnosis_codes': ['I10', 'E11.9'],
            'medications_prescribed': ['lisinopril 10mg', 'metformin 500mg'],
            'recommendations': 'Continue current medications, monitor BP daily, follow up in 4 weeks',
            'follow_up_required': True,
            'follow_up_date': timezone.now() + timedelta(weeks=4)
        },
        {
            'note_type': 'progress',
            'title': 'Progress Note - Week 2',
            'content': 'Patient reports good adherence to medications. BP readings show slight elevation. Discussed lifestyle modifications.',
            'recommendations': 'Increase exercise frequency, reduce sodium intake',
            'follow_up_required': False
        }
    ]
    
    for note_data in notes_data:
        note, created = ClinicalNote.objects.get_or_create(
            clinician=clinician_profile,
            patient=patient_profile,
            title=note_data['title'],
            defaults=note_data
        )
        if created:
            print(f"✓ Created clinical note: {note.title}")
    
    # Create treatment plan
    treatment_plan, created = TreatmentPlan.objects.get_or_create(
        clinician=clinician_profile,
        patient=patient_profile,
        title='Comprehensive Chronic Disease Management',
        defaults={
            'description': 'Integrated treatment plan for hypertension and diabetes management',
            'status': 'active',
            'priority': 'high',
            'goals': [
                'Maintain HbA1c < 7%',
                'Keep systolic BP < 130 mmHg',
                'Achieve 10% weight reduction'
            ],
            'interventions': [
                'Medication management',
                'Dietary counseling',
                'Exercise program',
                'Regular monitoring'
            ],
            'medications': ['lisinopril 10mg daily', 'metformin 500mg twice daily'],
            'lifestyle_modifications': [
                'DASH diet implementation',
                '150 minutes moderate exercise weekly',
                'Daily BP monitoring',
                'Weight tracking'
            ],
            'start_date': timezone.now(),
            'review_date': timezone.now() + timedelta(weeks=4),
            'progress_notes': 'Patient engaged and motivated',
            'adherence_score': 85
        }
    )
    if created:
        print(f"✓ Created treatment plan: {treatment_plan.title}")
    
    # Create stability score
    stability_score, created = StabilityScore.objects.get_or_create(
        patient=patient_profile,
        defaults={
            'score': 72.5,
            'risk_level': 'medium',
            'vital_signs_score': 75.0,
            'lifestyle_score': 70.0,
            'medication_adherence_score': 85.0,
            'symptom_burden_score': 80.0,
            'identified_risks': ['elevated_blood_pressure', 'medication_adherence_decline'],
            'risk_probability': 0.275,
            'model_version': '1.0',
            'calculation_method': 'rule_based',
            'confidence_level': 0.85,
            'data_freshness': timezone.now()
        }
    )
    if created:
        print(f"✓ Created stability score: {stability_score.score} ({stability_score.risk_level})")
    
    # Create health prediction
    prediction, created = HealthPrediction.objects.get_or_create(
        patient=patient_profile,
        prediction_type='blood_pressure_spike',
        time_horizon='7d',
        defaults={
            'probability': 0.35,
            'confidence': 0.75,
            'description': 'Elevated risk of blood pressure spike based on recent upward trend and stress levels',
            'key_factors': ['blood_pressure_trend', 'stress_level', 'medication_adherence'],
            'data_points_used': {'avg_systolic': 137, 'stress_level': 3.5, 'adherence': 83},
            'model_name': 'BP_Predictor',
            'model_version': '1.0',
            'expires_at': timezone.now() + timedelta(days=7)
        }
    )
    if created:
        print(f"✓ Created health prediction: {prediction.get_prediction_type_display()}")
    
    # Create smart nudges
    nudges_data = [
        {
            'category': 'medication',
            'priority': 'high',
            'title': 'Medication Reminder',
            'message': 'Your medication adherence has decreased to 83%. Consistent medication use is crucial for managing your hypertension.',
            'action_text': 'Set Reminders',
            'target_behavior': 'medication_adherence',
            'delivery_method': 'dashboard'
        },
        {
            'category': 'exercise',
            'priority': 'medium',
            'title': 'Stay Active',
            'message': 'Regular physical activity can help lower blood pressure. Consider a 30-minute walk today!',
            'action_text': 'Log Activity',
            'target_behavior': 'physical_activity',
            'delivery_method': 'dashboard'
        }
    ]
    
    for nudge_data in nudges_data:
        nudge_data['expires_at'] = timezone.now() + timedelta(days=3)
        nudge, created = SmartNudge.objects.get_or_create(
            patient=patient_profile,
            title=nudge_data['title'],
            defaults=nudge_data
        )
        if created:
            print(f"✓ Created smart nudge: {nudge.title}")
    
    # Create patient notes
    patient_notes_data = [
        {
            'note_type': 'general',
            'title': 'Medication Side Effects',
            'content': 'Experienced slight dizziness when standing up quickly. Possibly related to blood pressure medication.',
            'tags': ['medication', 'side_effects'],
            'is_automated': False
        },
        {
            'note_type': 'symptom',
            'title': 'Daily Energy Levels',
            'content': 'Feeling more energetic since starting the exercise routine. Sleep quality has also improved.',
            'tags': ['exercise', 'sleep', 'energy'],
            'is_automated': False
        }
    ]
    
    for note_data in patient_notes_data:
        patient_note, created = PatientNote.objects.get_or_create(
            patient=patient_profile,
            title=note_data['title'],
            defaults=note_data
        )
        if created:
            print(f"✓ Created patient note: {patient_note.title}")
    
    print("\n🎉 Test data creation completed successfully!")
    print("\nTest Accounts Created:")
    print(f"Admin: username='admin', password='admin123'")
    print(f"Patient: username='john_doe', password='patient123'")
    print(f"Clinician: username='dr_smith', password='doctor123'")
    print("\nDatabase now contains:")
    print(f"• {User.objects.count()} users")
    print(f"• {PatientProfile.objects.count()} patient profiles")
    print(f"• {ClinicianProfile.objects.count()} clinician profiles")
    print(f"• {VitalSigns.objects.count()} vital signs records")
    print(f"• {LifestyleMetrics.objects.count()} lifestyle metrics")
    print(f"• {HealthGoal.objects.count()} health goals")
    print(f"• {ClinicalNote.objects.count()} clinical notes")
    print(f"• {TreatmentPlan.objects.count()} treatment plans")
    print(f"• {StabilityScore.objects.count()} stability scores")
    print(f"• {HealthPrediction.objects.count()} health predictions")
    print(f"• {SmartNudge.objects.count()} smart nudges")

if __name__ == '__main__':
    create_test_data()