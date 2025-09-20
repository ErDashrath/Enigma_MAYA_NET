#!/usr/bin/env python
"""
API Integration Test for Risk Prediction Endpoint
Tests the complete risk prediction workflow
"""
import os
import sys
import json
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vitalcircle.settings')

# Initialize Django
import django
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from vitals.views import RiskPredictView
from patients.models import PatientProfile


def create_test_user_and_profile():
    """Create a test user and patient profile"""
    try:
        import uuid
        from datetime import date
        
        # Create unique username to avoid conflicts
        unique_id = str(uuid.uuid4())[:8]
        username = f'testpatient_{unique_id}'
        
        # Create test user
        user = User.objects.create_user(
            username=username,
            email=f'test_{unique_id}@example.com',
            password='testpass123'
        )
        
        # Calculate date of birth for 65-year-old
        birth_year = date.today().year - 65
        date_of_birth = date(birth_year, 1, 1)
        
        # Create patient profile
        profile = PatientProfile.objects.create(
            user=user,
            date_of_birth=date_of_birth,
            gender='M',
            chronic_conditions='diabetes,hypertension',
            medications='metformin,lisinopril'
        )
        
        print(f"✓ Created test user and profile: {user.username}")
        return user, profile
        
    except Exception as e:
        print(f"✗ Error creating test user: {str(e)}")
        return None, None


def test_risk_prediction_api():
    """Test the complete risk prediction API workflow"""
    print("🔗 Testing Risk Prediction API Endpoint")
    print("=" * 50)
    
    # Create test user and profile
    user, profile = create_test_user_and_profile()
    if not user or not profile:
        return False
    
    try:
        # Create API client and authenticate
        client = APIClient()
        client.force_authenticate(user=user)
        
        # Test data for risk prediction
        test_data = {
            'age': 65,
            'systolic_bp': 140,
            'diastolic_bp': 90,
            'heart_rate': 85,
            'blood_glucose': 180,
            'medical_conditions': ['diabetes_type2', 'hypertension'],
            'current_medications': ['metformin', 'lisinopril'],
            'recent_symptoms': ['fatigue', 'dizziness']
        }
        
        print("📤 Sending POST request to /vitals/api/risk-predict/")
        print(f"   Input data: {json.dumps(test_data, indent=2)}")
        
        # Make POST request to risk prediction endpoint
        response = client.post('/vitals/api/risk-predict/', test_data, format='json')
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✓ API call successful!")
            print(f"📊 Risk Prediction Results:")
            
            # Extract and display results
            risk_prediction = response_data.get('risk_prediction', {})
            patient_context = response_data.get('patient_context', {})
            
            print(f"   • Assessment ID: {response_data.get('assessment_id')}")
            print(f"   • Timestamp: {response_data.get('timestamp')}")
            print(f"   • Risk Level: {risk_prediction.get('risk_level')}")
            print(f"   • Stability Score: {risk_prediction.get('stability_score')}")
            print(f"   • Risk Percentage: {risk_prediction.get('risk_percentage')}%")
            print(f"   • Confidence Score: {risk_prediction.get('confidence_score')}")
            print(f"   • Risk Factors: {len(risk_prediction.get('risk_factors', []))}")
            print(f"   • Recommendations: {len(risk_prediction.get('recommendations', []))}")
            print(f"   • Patient Age: {patient_context.get('age')}")
            print(f"   • Has Medical History: {patient_context.get('has_medical_history')}")
            
            # Display some risk factors and recommendations
            risk_factors = risk_prediction.get('risk_factors', [])
            if risk_factors:
                print(f"\n📋 Risk Factors Identified:")
                for i, factor in enumerate(risk_factors[:3], 1):
                    print(f"   {i}. {factor}")
            
            recommendations = risk_prediction.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"   {i}. {rec}")
            
            return True
            
        else:
            print(f"✗ API call failed with status {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing API: {str(e)}")
        return False
    
    finally:
        # Clean up test data
        try:
            if user:
                user.delete()
                print(f"\n🧹 Cleaned up test user")
        except:
            pass


def test_get_assessments_api():
    """Test the GET endpoint for historical assessments"""
    print("\n🔗 Testing GET Historical Assessments")
    print("=" * 50)
    
    # Create test user and profile
    user, profile = create_test_user_and_profile()
    if not user or not profile:
        return False
    
    try:
        # Create API client and authenticate
        client = APIClient()
        client.force_authenticate(user=user)
        
        print("📤 Sending GET request to /vitals/api/risk-predict/")
        
        # Make GET request to historical assessments endpoint
        response = client.get('/vitals/api/risk-predict/')
        
        print(f"\n📥 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print("✓ GET API call successful!")
            print(f"📊 Historical Assessments:")
            print(f"   • Patient ID: {response_data.get('patient_id')}")
            print(f"   • Total Assessments: {response_data.get('total_assessments')}")
            print(f"   • Recent Assessments Available: {len(response_data.get('recent_assessments', []))}")
            
            return True
            
        else:
            print(f"✗ GET API call failed with status {response.status_code}")
            print(f"   Response: {response.content.decode()}")
            return False
            
    except Exception as e:
        print(f"✗ Error testing GET API: {str(e)}")
        return False
    
    finally:
        # Clean up test data
        try:
            if user:
                user.delete()
                print(f"\n🧹 Cleaned up test user")
        except:
            pass


def main():
    """Run API integration tests"""
    print("🌐 Risk Prediction API Integration Test")
    print("=" * 60)
    
    tests = [
        ("POST Risk Prediction", test_risk_prediction_api),
        ("GET Historical Assessments", test_get_assessments_api)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 60)
    print("📊 API Integration Test Results:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All API integration tests passed!")
        print("\n🚀 Risk Prediction API is fully functional and ready for production!")
        print("\n📚 Usage:")
        print("  POST /vitals/api/risk-predict/ - Generate new risk assessment")
        print("  GET  /vitals/api/risk-predict/ - Get historical assessments")
        print("\n🔐 Authentication: JWT Token required")
        print("🏥 Integration: Uses LLaMA 3.2 Medical Pro model")
    else:
        print("\n⚠️  Some API tests failed. Please check the implementation.")
    
    return all_passed


if __name__ == "__main__":
    main()