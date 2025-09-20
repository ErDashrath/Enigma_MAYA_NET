"""
Django management command to create test data for VitalCircle
Usage: python manage.py create_test_data
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta

from patients.models import PatientProfile, HealthGoal, PatientNote
from vitals.models import VitalSigns, LifestyleMetrics, SymptomReport
from ai_engine.models import StabilityScore, HealthPrediction, SmartNudge
from clinicians.models import ClinicianProfile, PatientAssignment, ClinicalNote, TreatmentPlan


class Command(BaseCommand):
    help = 'Create test data for VitalCircle application'

    def handle(self, *args, **options):
        self.stdout.write("Creating test data for VitalCircle...")
        
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
            self.stdout.write(self.style.SUCCESS(f"✓ Created admin user: {admin_user.username}"))
        else:
            self.stdout.write(f"✓ Admin user already exists: {admin_user.username}")
        
        # Create test patient user
        patient_user, created = User.objects.get_or_create(
            username='patient',
            defaults={
                'email': 'patient@vitalcircle.com',
                'first_name': 'John',
                'last_name': 'Doe',
            }
        )
        if created:
            patient_user.set_password('patient123')
            patient_user.save()
            self.stdout.write(self.style.SUCCESS(f"✓ Created patient user: {patient_user.username}"))
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("🎉 Basic test users created successfully!"))
        self.stdout.write("\nTest Accounts:")
        self.stdout.write(f"Admin: username='admin', password='admin123'")
        self.stdout.write(f"Patient: username='patient', password='patient123'")
        self.stdout.write("\nYou can now test login at: http://localhost:8000/login/")
        self.stdout.write("Database contains:")
        self.stdout.write(f"• {User.objects.count()} users total")