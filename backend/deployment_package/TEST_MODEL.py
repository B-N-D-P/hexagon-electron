#!/usr/bin/env python3
"""
Quick test script to verify the model works
Your friend can run this to test before deployment
"""

import joblib
import sys
from pathlib import Path

print("=" * 60)
print("TESTING TRAINED MODEL")
print("=" * 60)

try:
    # Try to load model files
    print("\n[1/4] Loading model files...")
    model = joblib.load('models/damage_classifier.pkl')
    print("    [OK] Model loaded: damage_classifier.pkl")
    
    scaler = joblib.load('models/feature_scaler.pkl')
    print("    [OK] Scaler loaded: feature_scaler.pkl")
    
    feature_names = joblib.load('models/feature_names.pkl')
    print("    [OK] Features loaded: feature_names.pkl")
    
    # Check model details
    print("\n[2/4] Model information:")
    print(f"    Algorithm: {type(model).__name__}")
    print(f"    Classes: {model.classes_}")
    print(f"    Features: {len(feature_names)} features")
    
    # Check if packages are available
    print("\n[3/4] Checking dependencies...")
    import numpy as np
    print("    [OK] numpy")
    import pandas as pd
    print("    [OK] pandas")
    from sklearn.ensemble import RandomForestClassifier
    print("    [OK] scikit-learn")
    
    # Create dummy test data
    print("\n[4/4] Testing prediction...")
    import numpy as np
    dummy_features = np.random.randn(1, len(feature_names))
    prediction = model.predict(dummy_features)
    probabilities = model.predict_proba(dummy_features)[0]
    
    print(f"    [OK] Prediction works!")
    print(f"    Test prediction: {prediction[0]}")
    print(f"    Test confidence: {max(probabilities)*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("[SUCCESS] MODEL IS READY TO USE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Use predict_example.py to test with real CSV data")
    print("2. Integrate into your web backend")
    print("3. Read DEPLOYMENT_PACKAGE_README.md for details")
    
except FileNotFoundError as e:
    print(f"\n[ERROR] File not found: {e}")
    print("\nMake sure you're in the correct directory with:")
    print("  models/damage_classifier.pkl")
    print("  models/feature_scaler.pkl")
    print("  models/feature_names.pkl")
    sys.exit(1)

except ImportError as e:
    print(f"\n[ERROR] Missing package: {e}")
    print("\nInstall required packages:")
    print("  pip install numpy pandas scikit-learn joblib")
    sys.exit(1)

except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    sys.exit(1)
