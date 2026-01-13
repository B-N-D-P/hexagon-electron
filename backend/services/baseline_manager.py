"""
Baseline profile management for comparative real-time monitoring.

Handles:
- Loading baseline/damage files from outputs/
- Caching baseline spectral signatures
- Marking live data as baseline
- Supporting multiple baselines for comparison
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import uuid
import numpy as np
from dataclasses import dataclass, asdict


@dataclass
class BaselineProfile:
    """Cached baseline profile data."""
    profile_id: str
    name: str
    created_at: str
    fs: float
    num_sensors: int
    
    # Spectral characteristics
    peaks: List[float]
    rms_baseline: Dict[int, float]
    psd_profile: Dict[str, List[float]]
    
    # Optional modal data
    frequencies: Optional[List[float]] = None
    damping_ratios: Optional[List[float]] = None
    mode_shapes: Optional[List[List[float]]] = None
    
    # Metadata
    source_file: Optional[str] = None
    description: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


class BaselineManager:
    """Manage baseline profiles for comparative analysis."""
    
    def __init__(self, outputs_dir: Path):
        """
        Initialize baseline manager.
        
        Args:
            outputs_dir: Path to outputs directory where baselines are saved
        """
        self.outputs_dir = Path(outputs_dir)
        self.outputs_dir.mkdir(exist_ok=True)
        
        # In-memory cache of baselines
        self.baselines: Dict[str, BaselineProfile] = {}
        self.current_baseline_id: Optional[str] = None
        
        # Load existing baselines
        self._scan_and_load_baselines()
    
    def _scan_and_load_baselines(self) -> None:
        """Scan outputs/ for existing baseline/damage files and load them."""
        try:
            # Look for JSON files with analysis results
            for json_file in self.outputs_dir.glob('*.json'):
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                    
                    # Check if this looks like a baseline/damage file
                    if self._is_baseline_file(data, json_file.name):
                        profile = self._parse_analysis_file(data, json_file.name)
                        if profile:
                            self.baselines[profile.profile_id] = profile
                            print(f"✓ Loaded baseline: {profile.name}")
                
                except Exception as e:
                    print(f"Warning: Could not load baseline from {json_file.name}: {e}")
        
        except Exception as e:
            print(f"Error scanning for baselines: {e}")
    
    def _is_baseline_file(self, data: Dict, filename: str) -> bool:
        """Check if a JSON file is a baseline/damage analysis."""
        # Check if it has the characteristic fields from analysis results
        if 'damaged_modal' in data or 'original_modal' in data:
            return True
        if 'damage_localization' in data:
            return True
        return False
    
    def _parse_analysis_file(self, data: Dict, filename: str) -> Optional[BaselineProfile]:
        """Parse an analysis JSON file into a BaselineProfile."""
        try:
            # Extract modal data
            modal_data = data.get('damaged_modal') or data.get('original_modal') or {}
            peaks = modal_data.get('frequencies', [])
            
            # Try to extract PSD and RMS
            psd_profile = {}
            rms_baseline = {}
            
            # Extract num_sensors from data or use default
            num_sensors = data.get('num_sensors', 5)
            
            # Create profile
            profile_id = str(uuid.uuid4())[:8]
            profile = BaselineProfile(
                profile_id=profile_id,
                name=f"Baseline_{filename.split('.')[0]}",
                created_at=datetime.utcnow().isoformat() + 'Z',
                fs=float(data.get('fs', 1000.0)),
                num_sensors=num_sensors,
                peaks=peaks,
                rms_baseline=rms_baseline,
                psd_profile=psd_profile,
                frequencies=peaks,
                damping_ratios=modal_data.get('damping_ratios', []),
                mode_shapes=modal_data.get('mode_shapes', []),
                source_file=filename,
                description=f"Loaded from {filename}"
            )
            
            return profile
        except Exception as e:
            print(f"Error parsing baseline file {filename}: {e}")
            return None
    
    def create_baseline_from_live(self, live_profile: Dict, name: str = None) -> BaselineProfile:
        """
        Create a new baseline from live monitoring data.
        
        Args:
            live_profile: Profile dictionary from live_buffer.capture_baseline_from_buffer()
            name: Optional name for baseline
            
        Returns:
            Created BaselineProfile
        """
        profile_id = str(uuid.uuid4())[:8]
        
        if name is None:
            name = f"LiveBaseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        profile = BaselineProfile(
            profile_id=profile_id,
            name=name,
            created_at=live_profile.get('ts', datetime.utcnow().isoformat() + 'Z'),
            fs=live_profile.get('fs', 1000.0),
            num_sensors=live_profile.get('num_sensors', 5),
            peaks=live_profile.get('peaks', []),
            rms_baseline=live_profile.get('rms_baseline', {}),
            psd_profile=live_profile.get('psd_profile', {}),
            description="Created from live monitoring"
        )
        
        # Store in cache
        self.baselines[profile_id] = profile
        
        # Save to file
        self._save_baseline_to_file(profile)
        
        return profile
    
    def _save_baseline_to_file(self, profile: BaselineProfile) -> str:
        """Save baseline profile to JSON file."""
        try:
            filename = f"baseline_{profile.profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.outputs_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            print(f"✓ Saved baseline to {filename}")
            return str(filepath)
        except Exception as e:
            print(f"Error saving baseline: {e}")
            return ""
    
    def get_baseline(self, baseline_id: str) -> Optional[BaselineProfile]:
        """Get a baseline by ID."""
        return self.baselines.get(baseline_id)
    
    def list_baselines(self) -> List[Dict]:
        """List all available baselines."""
        result = []
        for profile_id, profile in self.baselines.items():
            result.append({
                'id': profile_id,
                'name': profile.name,
                'created_at': profile.created_at,
                'fs': profile.fs,
                'num_peaks': len(profile.peaks),
                'description': profile.description
            })
        return result
    
    def set_current_baseline(self, baseline_id: str) -> bool:
        """Set the current baseline for comparative analysis."""
        if baseline_id in self.baselines:
            self.current_baseline_id = baseline_id
            return True
        return False
    
    def get_current_baseline(self) -> Optional[BaselineProfile]:
        """Get the current baseline profile."""
        if self.current_baseline_id:
            return self.baselines.get(self.current_baseline_id)
        return None
    
    def get_current_baseline_dict(self) -> Optional[Dict]:
        """Get current baseline as a dictionary (for live_buffer)."""
        profile = self.get_current_baseline()
        if profile:
            return profile.to_dict()
        return None
    
    def delete_baseline(self, baseline_id: str) -> bool:
        """Delete a baseline from memory."""
        if baseline_id in self.baselines:
            del self.baselines[baseline_id]
            if self.current_baseline_id == baseline_id:
                self.current_baseline_id = None
            return True
        return False
