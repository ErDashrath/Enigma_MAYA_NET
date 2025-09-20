"""
Script to view Supabase data content from Django
"""
import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile, VitalSigns, StabilityScore
from patients.models import Patient
from clinicians.models import Clinician

def view_all_data():
    """View all data in the database"""
    
    print("=" * 60)
    print("🏥 VITALCIRCLE DATABASE CONTENT")
    print("=" * 60)
    
    # Users
    print("\n👥 USERS:")
    print("-" * 40)
    users = User.objects.all()
    if users:
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Name: {user.first_name} {user.last_name}")
            print(f"Active: {user.is_active}")
            print(f"Staff: {user.is_staff}")
            print(f"Joined: {user.date_joined}")
            print("-" * 20)
    else:
        print("No users found")
    
    # User Profiles
    print("\n👤 USER PROFILES:")
    print("-" * 40)
    profiles = UserProfile.objects.all()
    if profiles:
        for profile in profiles:
            print(f"User: {profile.user.username}")
            print(f"Type: {profile.user_type}")
            print(f"Phone: {profile.phone_number}")
            print(f"Created: {profile.created_at}")
            print("-" * 20)
    else:
        print("No user profiles found")
    
    # Patients
    print("\n🏥 PATIENTS:")
    print("-" * 40)
    patients = Patient.objects.all()
    if patients:
        for patient in patients:
            print(f"ID: {patient.id}")
            print(f"User: {patient.user.username}")
            print(f"DOB: {patient.date_of_birth}")
            print(f"Phone: {patient.phone_number}")
            print(f"Emergency Contact: {patient.emergency_contact}")
            print(f"Conditions: {patient.medical_conditions}")
            print("-" * 20)
    else:
        print("No patients found")
    
    # Clinicians
    print("\n👨‍⚕️ CLINICIANS:")
    print("-" * 40)
    clinicians = Clinician.objects.all()
    if clinicians:
        for clinician in clinicians:
            print(f"ID: {clinician.id}")
            print(f"User: {clinician.user.username}")
            print(f"License: {clinician.license_number}")
            print(f"Specialization: {clinician.specialization}")
            print(f"Phone: {clinician.phone_number}")
            print("-" * 20)
    else:
        print("No clinicians found")
    
    # Vital Signs
    print("\n💓 VITAL SIGNS:")
    print("-" * 40)
    vitals = VitalSigns.objects.all()[:5]  # Show only first 5
    if vitals:
        for vital in vitals:
            print(f"Patient: {vital.patient.username}")
            print(f"BP: {vital.blood_pressure}")
            print(f"HR: {vital.heart_rate}")
            print(f"Stress: {vital.stress_level}")
            print(f"Sodium: {vital.sodium_intake}mg")
            print(f"Recorded: {vital.recorded_at}")
            print("-" * 20)
        
        total_vitals = VitalSigns.objects.count()
        if total_vitals > 5:
            print(f"... and {total_vitals - 5} more vital records")
    else:
        print("No vital signs found")
    
    # Stability Scores
    print("\n📊 STABILITY SCORES:")
    print("-" * 40)
    scores = StabilityScore.objects.all()[:5]  # Show only first 5
    if scores:
        for score in scores:
            print(f"Patient: {score.patient.username}")
            print(f"Score: {score.score}")
            print(f"Risk Level: {score.risk_level}")
            print(f"Calculated: {score.calculated_at}")
            print("-" * 20)
        
        total_scores = StabilityScore.objects.count()
        if total_scores > 5:
            print(f"... and {total_scores - 5} more stability scores")
    else:
        print("No stability scores found")
    
    # Summary
    print("\n📈 SUMMARY:")
    print("-" * 40)
    print(f"Total Users: {User.objects.count()}")
    print(f"Total Profiles: {UserProfile.objects.count()}")
    print(f"Total Patients: {Patient.objects.count()}")
    print(f"Total Clinicians: {Clinician.objects.count()}")
    print(f"Total Vital Records: {VitalSigns.objects.count()}")
    print(f"Total Stability Scores: {StabilityScore.objects.count()}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    view_all_data()