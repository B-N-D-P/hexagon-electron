# 🚀 ML Model Deployment Package

## 📦 What's in This Package

This package contains a **fully trained ML model** for structural damage classification using dual ADXL345 accelerometer sensors.

### **Model Performance**
- ✅ **Accuracy: 98.28%** on test data
- ✅ Trained on **230 labeled samples**
- ✅ Detects **5 damage categories**

---

## 📂 Files to Send to Your Friend

### **Required Files (MUST COPY):**
```
ml345/models/
├── damage_classifier.pkl    (231 KB) - The trained model
├── feature_scaler.pkl        (3.5 KB) - Feature normalization
└── feature_names.pkl         (1.1 KB) - Feature list

ml345/
├── predict_example.py        - Example prediction script
└── DEPLOYMENT_PACKAGE_README.md - This file
```

### **Optional Files (Helpful):**
```
ml345/data/labels/labels.csv  - Dataset information
ml345/train_complete.py       - Training script (if they want to retrain)
```

---

## 🎯 Damage Types Detected

| Category | Description | Examples |
|----------|-------------|----------|
| **healthy** | Undamaged structure | Baseline, repaired |
| **deformation** | Bent/deformed beams | Physical deformation |
| **bolt_damage** | Loose or missing bolts | Bolt 1-5 loose/removed |
| **missing_beam** | Structural beam missing | Beam 5,6,7,8,12 missing |
| **brace_damage** | Bracing removed | All braces removed |

---

## 💻 How Your Friend Can Use This

### **Option 1: Quick Test (Python Script)**

```python
import joblib
import numpy as np
import pandas as pd

# Load model
model = joblib.load('models/damage_classifier.pkl')
scaler = joblib.load('models/feature_scaler.pkl')
feature_names = joblib.load('models/feature_names.pkl')

# Extract features from sensor data (your friend implements this)
def extract_features(sensor_data):
    # sensor_data: CSV with columns S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g
    # Return dictionary of features (see predict_example.py for full code)
    pass

# Predict
features = extract_features(sensor_data)
features_scaled = scaler.transform([features_df])
prediction = model.predict(features_scaled)[0]
confidence = model.predict_proba(features_scaled)[0].max() * 100

print(f"Damage Type: {prediction}")
print(f"Confidence: {confidence:.1f}%")
```

### **Option 2: Use Provided Script**

```bash
# Test with sample data
python predict_example.py path/to/sensor_data.csv

# Output:
# >>> PREDICTION: healthy
# >>> CONFIDENCE: 95.3%
```

---

## 🌐 Integrate into Website (Flask/FastAPI)

### **Flask Example:**

```python
from flask import Flask, request, jsonify
import joblib
import numpy as np
import pandas as pd

app = Flask(__name__)

# Load model once at startup
model = joblib.load('models/damage_classifier.pkl')
scaler = joblib.load('models/feature_scaler.pkl')
feature_names = joblib.load('models/feature_names.pkl')

@app.route('/predict', methods=['POST'])
def predict_damage():
    # Receive sensor data from Arduino/frontend
    data = request.json['sensor_data']  # List of readings
    
    # Extract features (implement based on your needs)
    features = extract_features(data)
    features_df = pd.DataFrame([features])[feature_names]
    features_scaled = scaler.transform(features_df)
    
    # Predict
    prediction = model.predict(features_scaled)[0]
    probabilities = model.predict_proba(features_scaled)[0]
    
    return jsonify({
        'damage_type': prediction,
        'confidence': float(probabilities.max() * 100),
        'probabilities': {
            cls: float(prob * 100) 
            for cls, prob in zip(model.classes_, probabilities)
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### **FastAPI Example:**

```python
from fastapi import FastAPI
from pydantic import BaseModel
import joblib

app = FastAPI()

# Load model
model = joblib.load('models/damage_classifier.pkl')
scaler = joblib.load('models/feature_scaler.pkl')

class SensorData(BaseModel):
    readings: list  # List of sensor readings

@app.post('/api/predict')
async def predict(data: SensorData):
    features = extract_features(data.readings)
    features_scaled = scaler.transform([features])
    prediction = model.predict(features_scaled)[0]
    confidence = model.predict_proba(features_scaled)[0].max()
    
    return {
        "damage_type": prediction,
        "confidence": float(confidence * 100)
    }
```

---

## 📋 Requirements for Your Friend's Server

```txt
numpy>=1.24.0
pandas>=2.0.0
scikit-learn>=1.3.0
joblib>=1.3.0
```

Install with:
```bash
pip install numpy pandas scikit-learn joblib
```

---

## 🔧 Feature Extraction (Important!)

The model expects **these exact features** in this order (stored in `feature_names.pkl`):

For each sensor axis (S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g):
- `mean`, `std`, `min`, `max`, `range`, `rms`, `skew`, `kurtosis`
- `fft_mean`, `fft_max`, `fft_std` (frequency domain)

Plus cross-sensor features:
- `S1_magnitude`, `S2_magnitude`, `sensors_correlation`

**Total: 75 features**

See `predict_example.py` for complete implementation.

---

## 📊 Model Details

- **Algorithm**: Random Forest Classifier
- **Trees**: 100
- **Max Depth**: 20
- **Training Samples**: 230 files (172 train, 58 test)
- **Feature Count**: 75 statistical + frequency features
- **Input**: Dual ADXL345 accelerometer data (6 axes)

### **Top Important Features:**
1. S2_X_g_fft_max (5.8%)
2. S2_X_g_rms (5.6%)
3. S2_Z_g_std (5.1%)

---

## ✅ Testing the Model

```bash
# Test with baseline (healthy) data
python predict_example.py data/raw/baseline/data_20260119_142144.csv
# Expected: healthy (>95% confidence)

# Test with damaged data
python predict_example.py "data/raw/bolt loose damage/data_20260120_150026.csv"
# Expected: bolt_damage (>85% confidence)
```

---

## 🚀 Deployment Checklist

- [ ] Copy `models/*.pkl` files to server
- [ ] Install required packages (`numpy`, `pandas`, `scikit-learn`, `joblib`)
- [ ] Implement feature extraction from sensor data
- [ ] Create API endpoint for predictions
- [ ] Test with sample data
- [ ] Deploy to production!

---

## 🆘 Troubleshooting

**"No module named 'joblib'"**
→ `pip install joblib`

**"Feature mismatch error"**
→ Make sure you extract ALL 75 features in the correct order
→ Use `feature_names.pkl` to check expected feature list

**"Low confidence predictions"**
→ Ensure sensor data format matches training data (CSV with 6 columns)
→ Check data is in 'g' units (gravity units), not raw values

**"Wrong predictions"**
→ Verify sensor placement matches training setup
→ Ensure sampling rate is similar to training data

---

## 📞 Questions?

Model trained on: January 21, 2026
Accuracy: 98.28%
Contact: [Your contact info if needed]

**This model is PORTABLE and works on ANY computer with Python!** 🎉
