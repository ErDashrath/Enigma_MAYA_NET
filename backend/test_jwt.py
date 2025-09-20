"""
Test JWT Authentication functionality
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')
django.setup()

from django.contrib.auth.models import User
from core.auth import create_jwt_token, verify_jwt_token, JWTAuth
from datetime import datetime
import requests
import json

def test_jwt_functionality():
    """Test JWT token creation, verification, and API authentication"""
    
    print("🔐 TESTING JWT AUTHENTICATION")
    print("=" * 50)
    
    # 1. Test JWT Token Creation
    print("\n1️⃣ Testing JWT Token Creation...")
    try:
        # Get or create a test user
        user, created = User.objects.get_or_create(
            username='jwt_test_user',
            defaults={
                'email': 'jwt_test@example.com',
                'first_name': 'JWT',
                'last_name': 'Test'
            }
        )
        if created:
            user.set_password('testpassword123')
            user.save()
            print(f"✅ Created test user: {user.username}")
        else:
            print(f"✅ Using existing user: {user.username}")
        
        # Create JWT token
        token = create_jwt_token(user)
        print(f"✅ JWT Token created successfully")
        print(f"   Token length: {len(token)} characters")
        print(f"   Token preview: {token[:30]}...")
        
    except Exception as e:
        print(f"❌ JWT Token creation failed: {e}")
        return False
    
    # 2. Test JWT Token Verification
    print("\n2️⃣ Testing JWT Token Verification...")
    try:
        payload = verify_jwt_token(token)
        if payload:
            print(f"✅ JWT Token verified successfully")
            print(f"   User ID: {payload.get('user_id')}")
            print(f"   Username: {payload.get('username')}")
            exp_time = datetime.fromtimestamp(payload.get('exp'))
            print(f"   Expires: {exp_time}")
            print(f"   Valid for: {(exp_time - datetime.utcnow()).seconds} seconds")
        else:
            print("❌ JWT Token verification failed")
            return False
    except Exception as e:
        print(f"❌ JWT Token verification error: {e}")
        return False
    
    # 3. Test JWTAuth Class
    print("\n3️⃣ Testing JWTAuth Class...")
    try:
        jwt_auth = JWTAuth()
        
        # Create a mock request object
        class MockRequest:
            pass
        
        request = MockRequest()
        authenticated_user = jwt_auth.authenticate(request, token)
        
        if authenticated_user:
            print(f"✅ JWTAuth authentication successful")
            print(f"   Authenticated user: {authenticated_user.username}")
            print(f"   User ID: {authenticated_user.id}")
        else:
            print("❌ JWTAuth authentication failed")
            return False
    except Exception as e:
        print(f"❌ JWTAuth authentication error: {e}")
        return False
    
    # 4. Test API Login Endpoint
    print("\n4️⃣ Testing API Login Endpoint...")
    try:
        login_data = {
            "username": user.username,
            "password": "testpassword123"
        }
        
        # Test the login API
        response = requests.post(
            "http://127.0.0.1:8000/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            api_token = data.get('access_token')
            print(f"✅ API Login successful")
            print(f"   Status: {response.status_code}")
            print(f"   Token received: {bool(api_token)}")
            print(f"   User data: {data.get('user', {}).get('username')}")
            
            # Test the token with protected endpoint
            print("\n5️⃣ Testing Protected Endpoint...")
            headers = {"Authorization": f"Bearer {api_token}"}
            protected_response = requests.get(
                "http://127.0.0.1:8000/api/auth/me",
                headers=headers
            )
            
            if protected_response.status_code == 200:
                user_data = protected_response.json()
                print(f"✅ Protected endpoint access successful")
                print(f"   User: {user_data.get('username')}")
                print(f"   Email: {user_data.get('email')}")
            else:
                print(f"❌ Protected endpoint failed: {protected_response.status_code}")
                print(f"   Response: {protected_response.text}")
        else:
            print(f"❌ API Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - cannot test API endpoints")
        print("   Start server with: python manage.py runserver")
    except Exception as e:
        print(f"❌ API test error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 JWT AUTHENTICATION TESTS COMPLETED")
    return True

if __name__ == "__main__":
    test_jwt_functionality()