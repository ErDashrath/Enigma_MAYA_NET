#!/usr/bin/env python
"""
Script to ensure all users have a UserProfile
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/path/to/your/project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import UserProfile

def ensure_user_profiles():
    """Ensure all users have a UserProfile"""
    users_without_profile = []
    
    for user in User.objects.all():
        try:
            profile = user.userprofile
            print(f"✅ {user.username} has profile: {profile.user_type}")
        except UserProfile.DoesNotExist:
            users_without_profile.append(user)
            print(f"❌ {user.username} missing profile")
    
    if users_without_profile:
        print(f"\n🔧 Creating profiles for {len(users_without_profile)} users...")
        for user in users_without_profile:
            UserProfile.objects.create(
                user=user,
                user_type='patient'  # Default to patient
            )
            print(f"✅ Created profile for {user.username}")
    else:
        print("\n✅ All users have profiles!")

if __name__ == '__main__':
    ensure_user_profiles()