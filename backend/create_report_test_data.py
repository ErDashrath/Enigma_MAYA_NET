"""
Script to create dummy data for testing report endpoints
"""
import os
import django
from datetime import datetime, timedelta
from django.utils import timezone
import random

# Setup Django with SQLite for local development
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')
# Force SQLite usage by overriding database settings
import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': 'db.sqlite3',
            }
        },
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'core',
            'patients',
            'vitals',
            'ai_engine',
            'clinicians',
        ],
        SECRET_KEY='dummy-key-for-script',
        USE_TZ=True,
    )
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, PatientProfile, VitalSigns, StabilityScore, HealthNudge
from patients.models import PatientProfile as PatientsPatientProfile, HealthGoal
from vitals.models import VitalSigns as VitalsVitalSigns, LifestyleMetrics, SymptomReport, RiskAssessment
from ai_engine.models import MedicineAlert, MedicineIntake, AIHealthNudge

def create_dummy_users():
    """Create sample users and profiles"""
    print("Creating dummy users...")

    # Create patients
    patients_data = [
        {
            'username': 'john_doe',
            'email': 'john@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'date_of_birth': datetime(1985, 5, 15).date(),
            'gender': 'M',
            'chronic_conditions': ['hypertension', 'diabetes_type2'],
            'medications': ['Lisinopril 10mg', 'Metformin 500mg'],
        },
        {
            'username': 'jane_smith',
            'email': 'jane@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'date_of_birth': datetime(1990, 8, 22).date(),
            'gender': 'F',
            'chronic_conditions': ['asthma'],
            'medications': ['Albuterol inhaler'],
        },
        {
            'username': 'bob_johnson',
            'email': 'bob@example.com',
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'date_of_birth': datetime(1975, 12, 10).date(),
            'gender': 'M',
            'chronic_conditions': ['heart_disease'],
            'medications': ['Aspirin 81mg', 'Atorvastatin 20mg'],
        }
    ]

    patients = []
    for data in patients_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'email': data['email'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
            }
        )
        if created:
            user.set_password('password123')
            user.save()

        # Create UserProfile
        user_profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'user_type': 'patient'}
        )

        # Create PatientProfile (core)
        patient_profile, _ = PatientProfile.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': data['date_of_birth'],
                'phone_number': f'555-{random.randint(1000,9999)}',
                'medical_conditions': ', '.join(data['chronic_conditions']),
            }
        )

        # Create PatientProfile (patients app)
        patients_patient, _ = PatientsPatientProfile.objects.get_or_create(
            user=user,
            defaults={
                'date_of_birth': data['date_of_birth'],
                'gender': data['gender'],
                'chronic_conditions': data['chronic_conditions'],
                'medications': data['medications'],
                'current_stability_score': random.uniform(60, 90),
                'risk_level': random.choice(['low', 'medium', 'high']),
            }
        )

        patients.append(user)

    # Create clinician
    clinician_user, _ = User.objects.get_or_create(
        username='dr_smith',
        defaults={
            'email': 'dr.smith@example.com',
            'first_name': 'Dr. Smith',
            'last_name': 'Johnson',
        }
    )
    if _:
        clinician_user.set_password('password123')
        clinician_user.save()

    UserProfile.objects.get_or_create(
        user=clinician_user,
        defaults={'user_type': 'clinician'}
    )

    return patients

def create_vital_signs_data(patients):
    """Create sample vital signs data"""
    print("Creating vital signs data...")

    for patient in patients:
        # Create 30 days of vital signs data
        for days_ago in range(30):
            recorded_at = timezone.now() - timedelta(days=days_ago)

            # Core VitalSigns
            VitalSigns.objects.get_or_create(
                patient=patient,
                recorded_at__date=recorded_at.date(),
                defaults={
                    'systolic_bp': random.randint(110, 160),
                    'diastolic_bp': random.randint(70, 100),
                    'heart_rate': random.randint(60, 100),
                    'stress_level': random.randint(1, 10),
                    'sodium_intake': random.uniform(2000, 4000),
                    'weight': random.uniform(150, 200),
                    'recorded_at': recorded_at,
                }
            )

            # Vitals app VitalSigns
            VitalsVitalSigns.objects.get_or_create(
                patient=PatientsPatientProfile.objects.get(user=patient),
                measured_at__date=recorded_at.date(),
                defaults={
                    'systolic_bp': random.randint(110, 160),
                    'diastolic_bp': random.randint(70, 100),
                    'heart_rate': random.randint(60, 100),
                    'temperature': random.uniform(97.0, 99.0),
                    'weight': random.uniform(150, 200),
                    'blood_glucose': random.randint(80, 180),
                    'oxygen_saturation': random.randint(95, 100),
                    'measured_at': recorded_at,
                    'source': random.choice(['manual', 'device', 'wearable']),
                }
            )

def create_lifestyle_data(patients):
    """Create sample lifestyle metrics"""
    print("Creating lifestyle metrics...")

    for patient in patients:
        patient_profile = PatientsPatientProfile.objects.get(user=patient)

        for days_ago in range(7):
            recorded_at = timezone.now() - timedelta(days=days_ago)

            LifestyleMetrics.objects.get_or_create(
                patient=patient_profile,
                recorded_at__date=recorded_at.date(),
                defaults={
                    'stress_level': random.randint(1, 5),
                    'sleep_hours': random.uniform(5, 9),
                    'sleep_quality': random.randint(1, 5),
                    'sodium_intake': random.uniform(2000, 4000),
                    'water_intake': random.uniform(32, 128),
                    'calorie_intake': random.randint(1500, 2500),
                    'activity_level': random.randint(1, 5),
                    'exercise_minutes': random.randint(0, 120),
                    'steps_count': random.randint(2000, 15000),
                    'recorded_at': recorded_at,
                }
            )

def create_medication_data(patients):
    """Create sample medication data"""
    print("Creating medication data...")

    medications = [
        {'name': 'Lisinopril', 'dosage': '10mg', 'times_per_day': 1},
        {'name': 'Metformin', 'dosage': '500mg', 'times_per_day': 2},
        {'name': 'Albuterol', 'dosage': '90mcg', 'times_per_day': 1},
        {'name': 'Aspirin', 'dosage': '81mg', 'times_per_day': 1},
    ]

    for patient in patients:
        for med in medications[:2]:  # Give each patient 2 medications
            alert, _ = MedicineAlert.objects.get_or_create(
                patient=patient,
                medicine_name=med['name'],
                defaults={
                    'dosage': med['dosage'],
                    'alert_type': 'daily',
                    'times_per_day': med['times_per_day'],
                    'start_date': timezone.now().date() - timedelta(days=30),
                    'priority': random.choice(['low', 'medium', 'high']),
                }
            )

            # Create intake records for last 7 days
            for days_ago in range(7):
                scheduled_time = timezone.now() - timedelta(days=days_ago, hours=random.randint(8, 20))
                MedicineIntake.objects.get_or_create(
                    alert=alert,
                    scheduled_time__date=scheduled_time.date(),
                    defaults={
                        'patient': patient,
                        'scheduled_time': scheduled_time,
                        'status': random.choice(['taken', 'missed', 'late']),
                    }
                )

def create_risk_assessments(patients):
    """Create sample risk assessments"""
    print("Creating risk assessments...")

    for patient in patients:
        patient_profile = PatientsPatientProfile.objects.get(user=patient)

        for days_ago in range(0, 30, 7):  # Weekly assessments
            calculated_at = timezone.now() - timedelta(days=days_ago)

            RiskAssessment.objects.get_or_create(
                patient=patient_profile,
                calculated_at__date=calculated_at.date(),
                defaults={
                    'assessment_type': random.choice(['automated', 'manual']),
                    'stability_score': random.uniform(50, 95),
                    'risk_level': random.choice(['low', 'moderate', 'high']),
                    'time_horizon': random.choice(['24h', '7d', '30d']),
                    'adverse_event_risk': random.choice([True, False]),
                    'adverse_event_probability': random.uniform(0.1, 0.8),
                    'vital_signs_score': random.uniform(60, 90),
                    'lifestyle_score': random.uniform(50, 85),
                    'medication_adherence_score': random.uniform(70, 95),
                    'calculated_at': calculated_at,
                    'expires_at': calculated_at + timedelta(days=7),
                }
            )

def create_stability_scores(patients):
    """Create sample stability scores"""
    print("Creating stability scores...")

    for patient in patients:
        patient_profile = PatientsPatientProfile.objects.get(user=patient)

        for days_ago in range(0, 30, 3):  # Every 3 days
            calculated_at = timezone.now() - timedelta(days=days_ago)

            StabilityScore.objects.get_or_create(
                patient=patient_profile,
                calculated_at__date=calculated_at.date(),
                defaults={
                    'score': random.uniform(55, 90),
                    'risk_level': random.choice(['low', 'medium', 'high', 'critical']),
                    'vital_signs_score': random.uniform(60, 90),
                    'lifestyle_score': random.uniform(50, 85),
                    'medication_adherence_score': random.uniform(70, 95),
                    'symptom_burden_score': random.uniform(70, 95),
                    'risk_probability': random.uniform(0.1, 0.7),
                    'calculated_at': calculated_at,
                    'data_freshness': calculated_at,
                }
            )

def create_health_goals(patients):
    """Create sample health goals"""
    print("Creating health goals...")

    goals_data = [
        {'goal_type': 'blood_pressure', 'title': 'Maintain Blood Pressure', 'target_value': 120},
        {'goal_type': 'weight', 'title': 'Weight Management', 'target_value': 180},
        {'goal_type': 'exercise', 'title': 'Daily Exercise', 'target_value': 30},
        {'goal_type': 'medication', 'title': 'Medication Adherence', 'target_value': 95},
    ]

    for patient in patients:
        patient_profile = PatientsPatientProfile.objects.get(user=patient)

        for goal in goals_data[:2]:  # 2 goals per patient
            HealthGoal.objects.get_or_create(
                patient=patient_profile,
                goal_type=goal['goal_type'],
                title=goal['title'],
                defaults={
                    'description': f'Achieve target {goal["goal_type"]} of {goal["target_value"]}',
                    'target_value': goal['target_value'],
                    'current_value': random.uniform(goal['target_value'] * 0.7, goal['target_value'] * 1.1),
                    'unit': 'mmHg' if goal['goal_type'] == 'blood_pressure' else 'lbs' if goal['goal_type'] == 'weight' else 'minutes' if goal['goal_type'] == 'exercise' else '%',
                    'target_date': timezone.now().date() + timedelta(days=90),
                    'progress_percentage': random.uniform(30, 80),
                }
            )

def main():
    """Main function to create all dummy data"""
    print("Starting dummy data creation...")

    # Clear existing data (optional - uncomment if needed)
    # print("Clearing existing data...")
    # User.objects.filter(username__in=['john_doe', 'jane_smith', 'bob_johnson', 'dr_smith']).delete()

    patients = create_dummy_users()
    create_vital_signs_data(patients)
    create_lifestyle_data(patients)
    create_medication_data(patients)
    create_risk_assessments(patients)
    create_stability_scores(patients)
    create_health_goals(patients)

    print("Dummy data creation completed!")
    print(f"Created data for {len(patients)} patients")

if __name__ == '__main__':
    main()