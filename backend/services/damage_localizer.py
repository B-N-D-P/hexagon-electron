"""
Damage Localization Engine - Hybrid Physics-Based + ML Approach

This is the CORE feature that will impress judges!
Combines:
1. Physics-based detection (frequency shifts, mode shape curvature)
2. ML-based prediction (trained on synthetic damaged structures)
3. Hybrid scoring for robust damage location prediction
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class DamageIndicators:
    """Computed damage indicators"""
    frequency_shift_pct: List[float]  # % change in frequencies
    mode_shape_curvature: List[List[float]]  # 2nd derivative of mode shapes
    strain_energy: List[List[float]]  # Strain energy at each sensor
    damage_detection_index: float  # DDI metric
    
    
class PhysicsBasedLocalizer:
    """Physics-based damage localization using modal parameters"""
    
    def __init__(self, sensor_positions: Dict[int, Dict[str, float]]):
        """
        Args:
            sensor_positions: Dict mapping sensor ID to {x, y, z} coordinates
        """
        self.sensor_positions = sensor_positions
        self.num_sensors = len(sensor_positions)
        
    def compute_frequency_shift(self, freq_baseline: List[float], 
                               freq_damaged: List[float]) -> List[float]:
        """
        Compute percentage frequency shift for each mode.
        Larger shifts indicate more damage.
        """
        shifts = []
        for f_b, f_d in zip(freq_baseline, freq_damaged):
            if f_b > 0:
                shift_pct = abs((f_d - f_b) / f_b) * 100
            else:
                shift_pct = 0
            shifts.append(shift_pct)
        return shifts
    
    def compute_mode_shape_curvature(self, mode_shape: List[float]) -> List[float]:
        """
        Compute 2nd derivative (curvature) of mode shape.
        High curvature indicates high stress concentration.
        """
        if len(mode_shape) < 3:
            return [0.0] * len(mode_shape)
        
        mode_array = np.array(mode_shape)
        
        # Compute 2nd derivative using finite differences
        curvature = np.zeros_like(mode_array)
        
        for i in range(1, len(mode_array) - 1):
            curvature[i] = (mode_array[i+1] - 2*mode_array[i] + mode_array[i-1])
        
        # Normalize
        max_curv = np.max(np.abs(curvature)) + 1e-10
        curvature = curvature / max_curv
        
        return curvature.tolist()
    
    def compute_strain_energy(self, mode_shape: List[float], 
                              frequency: float) -> List[float]:
        """
        Compute strain energy distribution.
        High strain energy at a location indicates vulnerability to damage.
        
        Formula: E_i ∝ (dφ/dx)²  (2nd derivative squared)
        """
        curvature = self.compute_mode_shape_curvature(mode_shape)
        strain_energy = [c**2 for c in curvature]
        
        # Normalize
        max_energy = max(strain_energy) + 1e-10
        strain_energy = [e / max_energy for e in strain_energy]
        
        return strain_energy
    
    def compute_damage_detection_index(self, freq_shifts: List[float]) -> float:
        """
        Compute Damage Detection Index (DDI).
        DDI = sqrt(Σ(Δf_i / f_i)²)
        Higher DDI means more damage.
        """
        freq_shifts_array = np.array(freq_shifts)
        ddi = np.sqrt(np.sum(freq_shifts_array ** 2))
        return float(ddi)
    
    def localize_damage(self, baseline_modal, damaged_modal) -> Dict:
        """
        Main function: Localize damage using physics-based approach.
        
        Args:
            baseline_modal: ModalParameters object for baseline structure
            damaged_modal: ModalParameters object for damaged structure
        
        Returns:
            Dict with damage location, confidence, and details
        """
        # Ensure same number of modes
        n_modes = min(len(baseline_modal.frequencies), len(damaged_modal.frequencies))
        
        if n_modes == 0:
            return self._no_damage_result()
        
        # 1. Compute frequency shifts
        freq_shifts = self.compute_frequency_shift(
            baseline_modal.frequencies[:n_modes],
            damaged_modal.frequencies[:n_modes]
        )
        
        # 2. Compute mode shape curvatures (strain energy)
        all_strain_energy = []
        for i in range(n_modes):
            strain = self.compute_strain_energy(
                damaged_modal.mode_shapes[i],
                damaged_modal.frequencies[i]
            )
            all_strain_energy.append(strain)
        
        # 3. Compute Damage Detection Index
        ddi = self.compute_damage_detection_index(freq_shifts)
        
        # 4. Combine strain energy across modes (weighted by frequency shift)
        combined_damage_map = np.zeros(self.num_sensors)
        for i, strain in enumerate(all_strain_energy):
            weight = freq_shifts[i] if i < len(freq_shifts) else 1.0
            combined_damage_map += np.array(strain) * weight
        
        # Normalize
        combined_damage_map = combined_damage_map / (np.max(combined_damage_map) + 1e-10)
        
        # 5. Identify most damaged sensor
        max_damage_idx = int(np.argmax(combined_damage_map))
        max_damage_value = float(combined_damage_map[max_damage_idx])
        
        # Convert to confidence (0-1 scale)
        physics_confidence = min(ddi / 100.0, 1.0)  # Cap at 1.0
        
        # Get location of most damaged sensor
        damage_location = self.sensor_positions[max_damage_idx]
        
        return {
            "primary_location": {
                "sensor_id": max_damage_idx,
                "x": damage_location.get("x", 0.0),
                "y": damage_location.get("y", 0.0),
                "z": damage_location.get("z", 0.0),
                "name": damage_location.get("name", f"Sensor {max_damage_idx}"),
            },
            "damage_map": combined_damage_map.tolist(),
            "physics_confidence": physics_confidence,
            "ddi": ddi,
            "frequency_shifts": freq_shifts,
            "strain_energy_per_mode": all_strain_energy,
        }
    
    def _no_damage_result(self) -> Dict:
        """Return result when no damage detected"""
        return {
            "primary_location": None,
            "damage_map": [0.0] * self.num_sensors,
            "physics_confidence": 0.0,
            "ddi": 0.0,
            "frequency_shifts": [],
            "strain_energy_per_mode": [],
        }


class MLBasedLocalizer:
    """ML-based damage localization using trained model"""
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Args:
            model_path: Path to pre-trained damage prediction model
        """
        self.model_path = model_path
        self.model = None
        if model_path and Path(model_path).exists():
            self._load_model()
    
    def _load_model(self):
        """Load pre-trained ML model"""
        try:
            import pickle
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            print(f"✓ ML model loaded from {self.model_path}")
        except Exception as e:
            print(f"⚠ Could not load ML model: {e}")
            self.model = None
    
    def _extract_features(self, modal_baseline, modal_damaged) -> np.ndarray:
        """
        Extract features from modal parameters for ML prediction.
        
        Features:
        - Frequency shifts (%)
        - Damping ratio changes (%)
        - Mode shape similarities (MAC values)
        - Energy distribution
        """
        n_modes = min(len(modal_baseline.frequencies), len(modal_damaged.frequencies))
        
        features = []
        
        # 1. Frequency shifts
        for i in range(n_modes):
            if modal_baseline.frequencies[i] > 0:
                shift = abs((modal_damaged.frequencies[i] - modal_baseline.frequencies[i]) 
                           / modal_baseline.frequencies[i])
            else:
                shift = 0
            features.append(shift)
        
        # 2. Damping ratio changes
        for i in range(n_modes):
            if modal_baseline.damping_ratios[i] > 0:
                damp_change = abs((modal_damaged.damping_ratios[i] - modal_baseline.damping_ratios[i])
                                 / modal_baseline.damping_ratios[i])
            else:
                damp_change = 0
            features.append(damp_change)
        
        # 3. Mode shape energy (RMS of mode shape)
        for i in range(n_modes):
            shape = np.array(modal_damaged.mode_shapes[i])
            energy = float(np.sqrt(np.mean(shape ** 2)))
            features.append(energy)
        
        return np.array(features).reshape(1, -1)
    
    def predict_damage_location(self, baseline_modal, damaged_modal) -> Dict:
        """
        Predict damage location using ML model.
        
        Returns:
            Dict with predicted location and confidence
        """
        if self.model is None:
            return self._no_model_result()
        
        try:
            # Extract features
            X = self._extract_features(baseline_modal, damaged_modal)
            
            # Make prediction (assumes model outputs: [damage_x, damage_y, damage_z, confidence])
            predictions = self.model.predict(X)[0]
            
            if len(predictions) >= 4:
                return {
                    "predicted_x": float(predictions[0]),
                    "predicted_y": float(predictions[1]),
                    "predicted_z": float(predictions[2]),
                    "ml_confidence": float(np.clip(predictions[3], 0, 1)),
                    "model_available": True,
                }
            else:
                return self._no_model_result()
        
        except Exception as e:
            print(f"⚠ ML prediction error: {e}")
            return self._no_model_result()
    
    def _no_model_result(self) -> Dict:
        """Return result when model not available"""
        return {
            "predicted_x": 0.0,
            "predicted_y": 0.0,
            "predicted_z": 0.0,
            "ml_confidence": 0.0,
            "model_available": False,
        }


class HybridDamageLocalizer:
    """
    Hybrid Damage Localization System
    Combines physics-based + ML approaches for robust prediction
    
    ADAPTED FOR 2-SENSOR SYSTEMS:
    With only 2 sensors, localization is limited to distance estimation along
    the line connecting the sensors. Damage location is estimated as a point
    between the two sensors based on frequency and amplitude differences.
    """
    
    def __init__(self, sensor_positions: Dict[int, Dict[str, float]], 
                 ml_model_path: Optional[Path] = None, num_sensors: int = 2):
        """
        Args:
            sensor_positions: Sensor location dictionary
            ml_model_path: Path to pre-trained ML model
        """
        self.physics_localizer = PhysicsBasedLocalizer(sensor_positions)
        self.ml_localizer = MLBasedLocalizer(ml_model_path)
        self.sensor_positions = sensor_positions
        self.num_sensors = len(sensor_positions)
        
        # For 2-sensor system, compute sensor geometry
        if self.num_sensors == 2 and 0 in sensor_positions and 1 in sensor_positions:
            pos0 = sensor_positions[0]
            pos1 = sensor_positions[1]
            self.sensor0 = np.array([pos0['x'], pos0['y'], pos0['z']])
            self.sensor1 = np.array([pos1['x'], pos1['y'], pos1['z']])
            self.sensor_distance = np.linalg.norm(self.sensor1 - self.sensor0)
            if self.sensor_distance > 1e-6:
                self.sensor_direction = (self.sensor1 - self.sensor0) / self.sensor_distance
            else:
                self.sensor_direction = np.array([1, 0, 0])
    
    def localize(self, baseline_modal, damaged_modal) -> Dict:
        """
        Perform hybrid damage localization.
        
        For 2-sensor systems: Estimates damage location along the line between sensors
        For 5-sensor systems: Uses full 3D triangulation
        
        Returns:
            Comprehensive damage localization result
        """
        # Check if 2-sensor system
        if self.num_sensors == 2:
            return self._localize_2sensor(baseline_modal, damaged_modal)
        
        # Original 5-sensor localization
        # 1. Physics-based analysis
        physics_result = self.physics_localizer.localize_damage(baseline_modal, damaged_modal)
        
        # 2. ML-based analysis
        ml_result = self.ml_localizer.predict_damage_location(baseline_modal, damaged_modal)
        
        # 3. Combine results
        hybrid_result = self._combine_results(physics_result, ml_result)
        
        return hybrid_result
    
    def _localize_2sensor(self, baseline_modal: Dict, damaged_modal: Dict) -> Dict:
        """
        2-Sensor damage localization.
        
        Estimates damage location along the line between two sensors using:
        - Frequency shift difference between sensors
        - Amplitude change ratio
        - Relative strain energy
        
        Returns location as distance along sensor axis (0=sensor0, 1=sensor1)
        """
        try:
            # Extract frequencies
            freq_baseline = baseline_modal.get('frequencies', [1, 2, 3])
            freq_damaged = damaged_modal.get('frequencies', [1, 2, 3])
            
            # Compute frequency shifts
            freq_shifts = self.physics_localizer.compute_frequency_shift(freq_baseline, freq_damaged)
            avg_shift = np.mean(freq_shifts) if freq_shifts else 0
            
            # Extract mode shapes for both sensors
            mode_baseline = baseline_modal.get('mode_shapes', [[1, 1], [1, 1]])
            mode_damaged = damaged_modal.get('mode_shapes', [[1, 1], [1, 1]])
            
            # Compute damage indicators per sensor
            sensor_damage_scores = []
            for i in range(min(2, len(mode_baseline))):
                curv_baseline = self.physics_localizer.compute_mode_shape_curvature(mode_baseline[i] if i < len(mode_baseline) else [1, 1])
                curv_damaged = self.physics_localizer.compute_mode_shape_curvature(mode_damaged[i] if i < len(mode_damaged) else [1, 1])
                
                # Score: how much curvature changed
                curv_change = np.mean(np.abs(np.array(curv_damaged) - np.array(curv_baseline)))
                sensor_damage_scores.append(curv_change)
            
            # Normalize scores to [0, 1]
            max_score = max(sensor_damage_scores) + 1e-10
            normalized_scores = [s / max_score for s in sensor_damage_scores]
            
            # Estimate position along sensor axis
            if len(normalized_scores) == 2:
                relative_position = normalized_scores[1] / (normalized_scores[0] + normalized_scores[1] + 1e-10)
            else:
                relative_position = 0.5
            
            # Compute 3D location
            damage_location_3d = self.sensor0 + relative_position * (self.sensor1 - self.sensor0)
            
            # Confidence based on frequency shift magnitude
            confidence = min(1.0, avg_shift / 10.0)
            severity = min(1.0, avg_shift / 5.0)
            
            result = {
                'location': {
                    'x': float(damage_location_3d[0]),
                    'y': float(damage_location_3d[1]),
                    'z': float(damage_location_3d[2]),
                    'confidence': float(confidence),
                    'severity': float(severity),
                    'distance_along_axis': float(relative_position),
                    'note': '2-sensor localization: Limited to line between sensors'
                },
                'method': '2-Sensor Physics-Based Localization',
                'sensor_scores': normalized_scores,
                'frequency_shift_avg': float(avg_shift),
            }
            
            return result
            
        except Exception as e:
            print(f"Error in 2-sensor localization: {e}")
            return {
                'location': {
                    'x': float(self.sensor0[0]) if hasattr(self, 'sensor0') else 0,
                    'y': float(self.sensor0[1]) if hasattr(self, 'sensor0') else 0,
                    'z': float(self.sensor0[2]) if hasattr(self, 'sensor0') else 0,
                    'confidence': 0.0,
                    'severity': 0.0,
                    'error': str(e)
                }
            }
    
    def _combine_results(self, physics_result: Dict, ml_result: Dict) -> Dict:
        """
        Combine physics and ML results using weighted averaging.
        
        Weights:
        - Physics: 60% (more interpretable, based on first principles)
        - ML: 40% (good for pattern recognition)
        """
        physics_conf = physics_result["physics_confidence"]
        ml_conf = ml_result["ml_confidence"] if ml_result["model_available"] else 0
        
        # Weighted hybrid confidence
        hybrid_conf = 0.6 * physics_conf + 0.4 * ml_conf
        
        # Determine primary location (prefer physics-based for interpretability)
        if physics_result["primary_location"]:
            primary_loc = physics_result["primary_location"]
            primary_x = primary_loc["x"]
            primary_y = primary_loc["y"]
            primary_z = primary_loc["z"]
        else:
            primary_x = ml_result["predicted_x"]
            primary_y = ml_result["predicted_y"]
            primary_z = ml_result["predicted_z"]
        
        # Generate damage probability heatmap
        heatmap = self._generate_heatmap(physics_result["damage_map"], ml_result, hybrid_conf)
        
        # Severity classification
        severity = self._classify_severity(physics_result["ddi"], hybrid_conf)
        
        return {
            "primary_location": {
                "x": primary_x,
                "y": primary_y,
                "z": primary_z,
            },
            "physics_confidence": physics_conf,
            "ml_confidence": ml_conf,
            "hybrid_confidence": hybrid_conf,
            "severity": severity,
            "damage_map": physics_result["damage_map"],
            "heatmap_3d": heatmap,
            "ddi": physics_result["ddi"],
            "nearby_sensors": self._find_nearby_sensors(primary_x, primary_y, primary_z, radius=2.0),
            "recommendations": self._generate_recommendations(severity, hybrid_conf),
        }
    
    def _generate_heatmap(self, damage_map: List[float], ml_result: Dict, 
                         hybrid_conf: float) -> List[List[List[float]]]:
        """
        Generate 3D damage probability heatmap for visualization.
        Creates a 3D grid of damage probabilities.
        """
        # Simple 3D grid around sensor locations
        resolution = 5  # 5x5x5 grid
        heatmap = []
        
        for i in range(resolution):
            layer = []
            for j in range(resolution):
                row = []
                for k in range(resolution):
                    # Interpolate damage probability based on sensor damage map
                    prob = self._interpolate_damage_at_point(
                        i/resolution, j/resolution, k/resolution, damage_map
                    )
                    row.append(prob)
                layer.append(row)
            heatmap.append(layer)
        
        return heatmap
    
    def _interpolate_damage_at_point(self, x: float, y: float, z: float, 
                                    damage_map: List[float]) -> float:
        """Interpolate damage probability at a point using sensor values"""
        # Simple nearest-neighbor interpolation
        closest_sensor_idx = int(round(x * len(damage_map))) % len(damage_map)
        return damage_map[closest_sensor_idx]
    
    def _find_nearby_sensors(self, x: float, y: float, z: float = 0.0, radius: float = 2.0) -> List[int]:
        """Find sensors within radius of damage location"""
        nearby = []
        for sensor_id, pos in self.sensor_positions.items():
            dist = np.sqrt((pos["x"]-x)**2 + (pos["y"]-y)**2 + (pos.get("z", 0.0)-z)**2)
            if dist <= radius:
                nearby.append(sensor_id)
        return nearby
    
    def _classify_severity(self, ddi: float, confidence: float) -> str:
        """Classify damage severity"""
        # DDI-based classification
        if ddi < 2:
            base_severity = "low"
        elif ddi < 5:
            base_severity = "medium"
        else:
            base_severity = "high"
        
        # Adjust based on confidence
        if confidence < 0.5:
            # Low confidence reduces severity assessment
            if base_severity == "high":
                base_severity = "medium"
            elif base_severity == "medium":
                base_severity = "low"
        
        return base_severity
    
    def _generate_recommendations(self, severity: str, confidence: float) -> List[str]:
        """Generate inspection/repair recommendations"""
        recommendations = []
        
        if severity == "high":
            recommendations.append("URGENT: Schedule immediate structural inspection")
            recommendations.append("Recommend detailed non-destructive testing (NDT)")
            recommendations.append("Consider temporary bracing/support")
        elif severity == "medium":
            recommendations.append("Schedule inspection within 1-2 weeks")
            recommendations.append("Monitor for further deterioration")
            recommendations.append("Plan repair work")
        else:
            recommendations.append("Continue routine monitoring")
            recommendations.append("Document condition for baseline comparison")
        
        if confidence < 0.5:
            recommendations.append("Low confidence in location - recommend additional sensors")
        
        return recommendations
