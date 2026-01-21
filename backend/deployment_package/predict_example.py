#!/usr/bin/env python3
"""
Example script to use the trained model for predictions
Can be run on ANY computer with the .pkl files
"""

import joblib
import numpy as np
import pandas as pd
from pathlib import Path

def extract_features_from_csv(csv_path):
    """Extract features from a CSV file (same as training)"""
    df = pd.read_csv(csv_path)
    
    # Skip header row if duplicated
    if df.iloc[0].astype(str).str.contains('S1_X_g').any():
        df = df.iloc[1:].reset_index(drop=True)
    
    # Convert to numeric
    df = df.apply(pd.to_numeric, errors='coerce').dropna()
    
    features = {}
    
    # Extract features for each column
    for col in df.columns:
        data = df[col].values
        
        # Time domain features
        features[f'{col}_mean'] = np.mean(data)
        features[f'{col}_std'] = np.std(data)
        features[f'{col}_min'] = np.min(data)
        features[f'{col}_max'] = np.max(data)
        features[f'{col}_range'] = np.max(data) - np.min(data)
        features[f'{col}_rms'] = np.sqrt(np.mean(data**2))
        features[f'{col}_skew'] = pd.Series(data).skew()
        features[f'{col}_kurtosis'] = pd.Series(data).kurtosis()
        
        # Frequency domain features
        fft = np.fft.fft(data)
        fft_mag = np.abs(fft)[:len(data)//2]
        features[f'{col}_fft_mean'] = np.mean(fft_mag)
        features[f'{col}_fft_max'] = np.max(fft_mag)
        features[f'{col}_fft_std'] = np.std(fft_mag)
    
    # Cross-sensor features
    features['S1_magnitude'] = np.mean(np.sqrt(df['S1_X_g']**2 + df['S1_Y_g']**2 + df['S1_Z_g']**2))
    features['S2_magnitude'] = np.mean(np.sqrt(df['S2_X_g']**2 + df['S2_Y_g']**2 + df['S2_Z_g']**2))
    features['sensors_correlation'] = df['S1_Z_g'].corr(df['S2_Z_g'])
    
    return features

def predict_damage(csv_path, model_dir='models'):
    """Predict damage type from sensor data CSV"""
    
    # Load trained model and scaler
    model = joblib.load(Path(model_dir) / 'damage_classifier.pkl')
    scaler = joblib.load(Path(model_dir) / 'feature_scaler.pkl')
    feature_names = joblib.load(Path(model_dir) / 'feature_names.pkl')
    
    # Extract features
    features = extract_features_from_csv(csv_path)
    
    # Convert to DataFrame with correct column order
    features_df = pd.DataFrame([features])[feature_names]
    
    # Scale features
    features_scaled = scaler.transform(features_df)
    
    # Predict
    prediction = model.predict(features_scaled)[0]
    probabilities = model.predict_proba(features_scaled)[0]
    
    # Get class names
    classes = model.classes_
    
    return {
        'prediction': prediction,
        'confidence': max(probabilities) * 100,
        'probabilities': dict(zip(classes, probabilities * 100))
    }

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python predict_example.py <path_to_csv>")
        print("\nExample:")
        print("  python predict_example.py data/raw/baseline/data_20260119_142144.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    print("=" * 60)
    print("DAMAGE PREDICTION")
    print("=" * 60)
    print(f"\nAnalyzing: {csv_file}")
    
    result = predict_damage(csv_file)
    
    print(f"\n>>> PREDICTION: {result['prediction']}")
    print(f">>> CONFIDENCE: {result['confidence']:.1f}%")
    
    print(f"\nAll probabilities:")
    for damage_type, prob in sorted(result['probabilities'].items(), key=lambda x: x[1], reverse=True):
        print(f"  {damage_type:20s}: {prob:5.1f}%")
    
    print("\n" + "=" * 60)
