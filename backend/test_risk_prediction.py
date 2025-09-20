#!/usr/bin/env python
"""
Test script for risk prediction API integration
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

def test_llama_runner():
    """Test the LLaMA runner integration"""
    try:
        from model_runner.llama_runner import LlamaRunner
        
        # Initialize LLaMA runner
        llama = LlamaRunner()
        print("✓ LLaMA runner initialized successfully")
        
        # Test sample input data
        test_data = {
            'age': 65,
            'systolic_bp': 140,
            'diastolic_bp': 90,
            'heart_rate': 85,
            'blood_glucose': 180,
            'medical_conditions': ['diabetes', 'hypertension'],
            'medications': ['metformin', 'lisinopril'],
            'symptoms': ['fatigue', 'dizziness']
        }
        
        # Run prediction
        result = llama.predict_medical_risk(test_data)
        print("✓ Risk prediction completed successfully")
        print(f"  - Risk Level: {result['risk_level']}")
        print(f"  - Stability Score: {result['stability_score']}")
        print(f"  - Risk Percentage: {result['risk_percentage']}%")
        print(f"  - Risk Factors: {len(result['risk_factors'])} identified")
        print(f"  - Recommendations: {len(result['recommendations'])} provided")
        
        return True
        
    except Exception as e:
        print(f"✗ LLaMA runner test failed: {str(e)}")
        return False

def test_serializers():
    """Test the API serializers"""
    try:
        from vitals.serializers import RiskInputSerializer, RiskOutputSerializer
        
        # Test input serializer
        test_input = {
            'age': 65,
            'systolic_bp': 140,
            'diastolic_bp': 90,
            'heart_rate': 85,
            'blood_glucose': 180,
            'medical_conditions': ['diabetes'],
            'current_medications': ['metformin'],
            'recent_symptoms': ['fatigue']
        }
        
        input_serializer = RiskInputSerializer(data=test_input)
        if input_serializer.is_valid():
            print("✓ Input serializer validation passed")
        else:
            print(f"✗ Input serializer validation failed: {input_serializer.errors}")
            return False
        
        # Test output serializer
        test_output = {
            'risk_prediction': {
                'binary_risk_label': '0',
                'stability_score': '72'
            },
            'explainability': {
                'key_factors': ['elevated_glucose', 'hypertension']
            }
        }
        
        output_serializer = RiskOutputSerializer(data=test_output)
        if output_serializer.is_valid():
            print("✓ Output serializer validation passed")
        else:
            print(f"✗ Output serializer validation failed: {output_serializer.errors}")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Serializer test failed: {str(e)}")
        return False

def test_models():
    """Test model imports and basic functionality"""
    try:
        from vitals.models import VitalSigns, LifestyleMetrics, MedicalHistory, RiskAssessment
        from patients.models import PatientProfile
        from django.contrib.auth.models import User
        
        print("✓ All models imported successfully")
        
        # Test model field access
        if hasattr(VitalSigns, 'blood_glucose'):
            print("✓ VitalSigns.blood_glucose field exists")
        else:
            print("✗ VitalSigns.blood_glucose field missing")
            
        if hasattr(RiskAssessment, 'assessment_type'):
            print("✓ RiskAssessment.assessment_type field exists")
        else:
            print("✗ RiskAssessment.assessment_type field missing")
            
        return True
        
    except Exception as e:
        print(f"✗ Model test failed: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Risk Prediction API Implementation")
    print("=" * 50)
    
    tests = [
        ("Models Import", test_models),
        ("API Serializers", test_serializers), 
        ("LLaMA Runner", test_llama_runner)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Testing {test_name}...")
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    all_passed = True
    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {test_name}: {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! Risk prediction API is ready.")
        print("\n📡 API Endpoint Available:")
        print("  POST /vitals/api/risk-predict/")
        print("  GET  /vitals/api/risk-predict/")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
    
    return all_passed

if __name__ == "__main__":
    main()