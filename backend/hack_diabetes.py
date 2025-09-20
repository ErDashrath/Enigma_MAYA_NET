# -*- coding: utf-8 -*-
"""
Diabetes Risk Prediction Model
Integrated with Django Ninja workflow for diabetes risk assessment
"""

import pandas as pd
import numpy as np
import warnings
import os
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn import svm
from sklearn.metrics import accuracy_score
from typing import Dict, Any, Tuple

warnings.filterwarnings('ignore')


class DiabetesRiskModel:
    """
    Diabetes Risk Prediction using SVM Classifier
    Integrated into the existing Web-LLM Django Ninja workflow
    """
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.classifier = svm.SVC(kernel='linear', probability=True, random_state=42)
        self.is_trained = False
        self._setup_model()
    
    def _setup_model(self):
        """Setup and train the diabetes model with built-in dataset"""
        # Load diabetes dataset from URL or create synthetic data for demo
        try:
            # Try to load from URL (Pima Indians Diabetes Dataset)
            url = "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv"
            columns = ['Pregnancies', 'Glucose', 'BloodPressure', 'SkinThickness', 
                      'Insulin', 'BMI', 'DiabetesPedigreeFunction', 'Age', 'Outcome']
            data = pd.read_csv(url, names=columns)
        except:
            # Fallback to synthetic data if internet is not available
            data = self._create_synthetic_data()
        
        # Prepare features and target
        X = data.drop(columns='Outcome', axis=1)
        Y = data['Outcome']
        
        # Train scaler and transform data
        self.scaler.fit(X)
        X_standardized = self.scaler.transform(X)
        
        # Split data
        X_train, X_test, Y_train, Y_test = train_test_split(
            X_standardized, Y, test_size=0.2, stratify=Y, random_state=2
        )
        
        # Train classifier
        self.classifier.fit(X_train, Y_train)
        self.is_trained = True
        
        # Calculate accuracy
        train_accuracy = accuracy_score(Y_train, self.classifier.predict(X_train))
        test_accuracy = accuracy_score(Y_test, self.classifier.predict(X_test))
        
        print(f"Diabetes Model Training Complete:")
        print(f"Training Accuracy: {train_accuracy:.4f}")
        print(f"Test Accuracy: {test_accuracy:.4f}")
    
    def _create_synthetic_data(self) -> pd.DataFrame:
        """Create synthetic diabetes data for training if dataset unavailable"""
        np.random.seed(42)
        n_samples = 768
        
        # Generate synthetic features
        pregnancies = np.random.poisson(3, n_samples)
        glucose = np.random.normal(120, 30, n_samples)
        bp = np.random.normal(70, 15, n_samples)
        skin_thickness = np.random.normal(20, 10, n_samples)
        insulin = np.random.normal(80, 40, n_samples)
        bmi = np.random.normal(32, 8, n_samples)
        dpf = np.random.exponential(0.5, n_samples)
        age = np.random.normal(33, 12, n_samples)
        
        # Create outcome based on risk factors
        risk_score = (
            (glucose > 140) * 0.4 +
            (bmi > 30) * 0.3 +
            (age > 50) * 0.2 +
            (bp > 80) * 0.1
        )
        outcome = (risk_score + np.random.normal(0, 0.2, n_samples) > 0.5).astype(int)
        
        data = pd.DataFrame({
            'Pregnancies': pregnancies,
            'Glucose': glucose,
            'BloodPressure': bp,
            'SkinThickness': skin_thickness,
            'Insulin': insulin,
            'BMI': bmi,
            'DiabetesPedigreeFunction': dpf,
            'Age': age,
            'Outcome': outcome
        })
        
        return data
    
    def predict_diabetes_risk(self, patient_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict diabetes risk for a patient
        
        Args:
            patient_data: Dict containing patient parameters
                - pregnancies: Number of pregnancies
                - glucose: Glucose level (mg/dL)
                - blood_pressure: Blood pressure (mmHg)
                - skin_thickness: Skin thickness (mm)
                - insulin: Insulin level (mu U/ml)
                - bmi: Body Mass Index
                - diabetes_pedigree_function: Diabetes pedigree function
                - age: Age in years
        
        Returns:
            Dict with diabetes risk assessment in exact JSON format requested
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call _setup_model() first.")
        
        # Extract and validate input parameters
        try:
            input_array = np.array([[
                patient_data.get('pregnancies', 0),
                patient_data.get('glucose', 100),
                patient_data.get('blood_pressure', patient_data.get('systolic', 70)),
                patient_data.get('skin_thickness', 20),
                patient_data.get('insulin', 80),
                patient_data.get('bmi', 25),
                patient_data.get('diabetes_pedigree_function', 0.3),
                patient_data.get('age', 30)
            ]])
        except Exception as e:
            raise ValueError(f"Invalid input data: {e}")
        
        # Standardize input data
        input_standardized = self.scaler.transform(input_array)
        
        # Get prediction probabilities
        prediction_proba = self.classifier.predict_proba(input_standardized)
        diabetes_probability = prediction_proba[0][1]  # Probability of diabetes
        
        # Make binary prediction
        prediction = self.classifier.predict(input_standardized)[0]
        
        # Determine risk level based on probability
        if diabetes_probability < 0.3:
            risk_level = "Low Risk"
        elif diabetes_probability < 0.7:
            risk_level = "Medium Risk"
        else:
            risk_level = "High Risk"
        
        # Create diagnosis label
        if prediction == 1:
            diagnosis_label = "The person is diabetic"
        else:
            diagnosis_label = "The person is not diabetic"
        
        # Return in exact JSON format requested
        return {
            "stability_score": float(diabetes_probability),
            "diagnosis_label": diagnosis_label,
            "risk_level": risk_level
        }


# Global instance for reuse
_diabetes_model_instance = None


def get_diabetes_model() -> DiabetesRiskModel:
    """Get singleton instance of diabetes model"""
    global _diabetes_model_instance
    if _diabetes_model_instance is None:
        _diabetes_model_instance = DiabetesRiskModel()
    return _diabetes_model_instance


# Legacy code for backwards compatibility (preserved but not used in integration)
if __name__ == "__main__":
    # This section contains the original notebook code for reference
    print("Diabetes Risk Model - Testing")
    
    # Example usage
    model = get_diabetes_model()
    
    # Test with sample data
    sample_patient = {
        'pregnancies': 5,
        'glucose': 166,
        'blood_pressure': 72,
        'skin_thickness': 19,
        'insulin': 175,
        'bmi': 25.8,
        'diabetes_pedigree_function': 0.587,
        'age': 51
    }
    
    result = model.predict_diabetes_risk(sample_patient)
    print("Sample prediction result:", result)