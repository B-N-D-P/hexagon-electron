# 🔍 Damage Classification Integration Guide

## Overview

A high-accuracy ML model (98.28%) has been integrated into your structural repair analysis website to automatically classify 5 types of structural damage from sensor data.

## 🎯 Detected Damage Types

| Type | Description | Severity |
|------|-------------|----------|
| **healthy** | No structural damage detected | None |
| **deformation** | Bent or deformed structural beams | High |
| **bolt_damage** | Loose or missing bolt connections | Medium |
| **missing_beam** | Structural member missing or removed | Critical |
| **brace_damage** | Lateral bracing system damaged | High |

## 📁 Files Added

### Backend Service
- `services/damage_classifier.py` - Main classification service
- `ml_models/damage_classifier/` - Trained model files (3 .pkl files)
  - `damage_classifier.pkl` (236 KB) - Random Forest model
  - `feature_scaler.pkl` (3.5 KB) - Feature normalization
  - `feature_names.pkl` (1.1 KB) - Feature names

### API Integration
- **New endpoint:** `POST /api/v1/classify-damage`
- **New schemas:** `DamageClassificationRequest`, `DamageClassificationResponse`
- **Health check updated:** Shows damage classifier status

### Frontend
- `damage_specification.html` - Beautiful UI for damage classification

## 🚀 Quick Start

### 1. Start the API Server

```bash
python app.py
```

The server will automatically load the damage classifier on startup.

### 2. Open the Frontend

Open `damage_specification.html` in your browser:

```bash
# If you have a simple HTTP server
python -m http.server 8080
# Then visit: http://localhost:8080/damage_specification.html
```

Or open the file directly in your browser.

### 3. Upload and Classify

1. Upload a CSV file with 6 columns: `S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g`
2. Click "Classify Damage"
3. View the results with confidence scores and recommendations

## 📡 API Usage

### Check Service Status

```bash
curl http://localhost:8000/health
```

Response includes:
```json
{
  "damage_classifier_available": true,
  "services": {
    "damage_classifier": "available"
  }
}
```

### Upload Sensor Data

```bash
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@sensor_data.csv"
```

Response:
```json
{
  "file_id": "abc12345",
  "filename": "sensor_data.csv",
  "num_samples": 2000,
  "num_sensors": 2
}
```

### Classify Damage

```bash
curl -X POST http://localhost:8000/api/v1/classify-damage \
  -H "Content-Type: application/json" \
  -d '{"file_id": "abc12345"}'
```

Response:
```json
{
  "file_id": "abc12345",
  "filename": "sensor_data.csv",
  "prediction": "bolt_damage",
  "confidence": 87.5,
  "probabilities": {
    "bolt_damage": 87.5,
    "healthy": 8.2,
    "deformation": 2.1,
    "missing_beam": 1.5,
    "brace_damage": 0.7
  },
  "top_3_predictions": [
    {"damage_type": "bolt_damage", "probability": 87.5},
    {"damage_type": "healthy", "probability": 8.2},
    {"damage_type": "deformation", "probability": 2.1}
  ],
  "damage_info": {
    "title": "Bolt Connection Damage",
    "severity": "Medium",
    "description": "Loose or missing bolts detected...",
    "recommendation": "Tighten or replace loose/missing bolts...",
    "icon": "🔩",
    "color": "orange"
  },
  "model_info": {
    "accuracy": 98.28,
    "algorithm": "Random Forest",
    "features_used": 69
  }
}
```

## 🔧 Python API Usage

### Basic Classification

```python
from services.damage_classifier import get_damage_classifier

# Get classifier instance
classifier = get_damage_classifier()

# Classify from CSV file
result = classifier.predict_from_csv('path/to/sensor_data.csv')

print(f"Damage Type: {result['prediction']}")
print(f"Confidence: {result['confidence']:.1f}%")
```

### From NumPy Array

```python
import numpy as np

# Your sensor data (2000+ samples, 6 channels)
sensor_data = np.random.randn(2000, 6)

# Classify
result = classifier.predict_from_array(sensor_data)

# Get damage description
damage_info = classifier.get_damage_description(result['prediction'])
print(damage_info['title'])
print(damage_info['recommendation'])
```

### From Pandas DataFrame

```python
import pandas as pd

# Load data
df = pd.read_csv('sensor_data.csv')

# Extract features and classify
features = classifier.extract_features_from_dataframe(df)
result = classifier.predict(features)
```

## 🎨 Frontend Features

The `damage_specification.html` provides:

- **Drag & Drop Upload** - Easy file upload interface
- **Real-time Classification** - Instant results after upload
- **Visual Results** - Color-coded damage severity
- **Confidence Scores** - Probability breakdown for all damage types
- **Recommendations** - Actionable advice based on damage type
- **Responsive Design** - Works on desktop and mobile
- **Beautiful UI** - Modern gradient design with animations

## 🧪 Testing

### Test the Model

```bash
cd deployment_package
python TEST_MODEL.py
```

### Test with Example Data

```bash
python deployment_package/predict_example.py outputs/baseline_*.json
```

### Run Integration Test

```python
python << 'EOF'
from services.damage_classifier import get_damage_classifier
import pandas as pd
import numpy as np

classifier = get_damage_classifier()

# Create test data
data = pd.DataFrame({
    'S1_X_g': np.random.randn(2000) * 0.1,
    'S1_Y_g': np.random.randn(2000) * 0.1,
    'S1_Z_g': np.random.randn(2000) * 0.1,
    'S2_X_g': np.random.randn(2000) * 0.1,
    'S2_Y_g': np.random.randn(2000) * 0.1,
    'S2_Z_g': np.random.randn(2000) * 0.1,
})

result = classifier.predict_from_array(data.values)
print(f"✅ Test passed! Predicted: {result['prediction']}")
EOF
```

## 📊 Model Details

- **Algorithm:** Random Forest Classifier (100 trees, max depth 20)
- **Training Data:** 230 labeled samples (172 train, 58 test)
- **Features:** 69 statistical and frequency domain features
- **Accuracy:** 98.28% on test data
- **Input Format:** CSV with 6 columns (dual ADXL345 accelerometers)

### Feature Extraction

The model extracts 69 features from sensor data:

**For each axis (S1_X, S1_Y, S1_Z, S2_X, S2_Y, S2_Z):**
- Time domain: mean, std, min, max, range, rms, skew, kurtosis
- Frequency domain: fft_mean, fft_max, fft_std

**Cross-sensor features:**
- S1_magnitude, S2_magnitude, sensors_correlation

## 🔗 Integration with Existing Features

The damage classifier works alongside your existing features:

1. **Repair Quality Analysis** - Use classifier to identify damage before repair
2. **Baseline Prediction** - Classify damage severity for ML456 baseline prediction
3. **Damage Localization** - Identify damage type before localizing
4. **Live Monitoring** - Real-time damage classification from sensor streams

## 🎯 Use Cases

### 1. Pre-Repair Assessment
```python
# Upload damaged structure data
# Classify damage type
# Use classification to guide repair strategy
```

### 2. Post-Repair Verification
```python
# Upload repaired structure data
# Check if classification shows "healthy"
# Validate repair quality
```

### 3. Automated Monitoring
```python
# Continuously monitor structure
# Alert when classification changes from "healthy"
# Track damage progression
```

## 📝 Notes

- Model requires sensor data with at least 512 samples
- Best results with 2000+ samples (matching training data)
- CSV format must match: S1_X_g, S1_Y_g, S1_Z_g, S2_X_g, S2_Y_g, S2_Z_g
- No timestamp column required
- Data should be in gravity units (g)

## 🆘 Troubleshooting

### Model Not Loading
```python
from services.damage_classifier import get_damage_classifier

classifier = get_damage_classifier()
print(f"Model loaded: {classifier.is_loaded}")
```

If False, check:
- Model files exist in `ml_models/damage_classifier/`
- Required packages installed: `numpy`, `pandas`, `scikit-learn`, `joblib`

### Low Confidence Predictions
- Ensure sensor data format matches training data
- Check data is in gravity units (g), not raw values
- Verify sensor placement matches training setup
- Ensure sufficient samples (2000+ recommended)

### API Connection Issues
- Ensure FastAPI server is running on port 8000
- Check CORS settings if accessing from different origin
- Verify file upload completed successfully before classification

## 📚 Additional Resources

- Model training details: `deployment_package/DEPLOYMENT_PACKAGE_README.md`
- API documentation: http://localhost:8000/docs
- Test scripts: `deployment_package/TEST_MODEL.py` and `predict_example.py`

---

**Model trained:** January 21, 2026  
**Integration completed:** January 21, 2026  
**Accuracy:** 98.28% ✨
