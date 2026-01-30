#!/usr/bin/env python3
"""
Train ML456 Advanced models with your 12-gate data
"""
import sys
import os
import shutil
import zipfile
from pathlib import Path

# Add ml456_advanced to path
ml456_path = Path('/home/itachi/ml456_advanced')
if not ml456_path.exists():
    print(f"❌ Error: ml456_advanced not found at {ml456_path}")
    sys.exit(1)

sys.path.insert(0, str(ml456_path))

def prepare_data_for_ml456(zip_path, output_dir):
    """Extract and organize data for ml456_advanced training."""
    print("📦 Preparing data for ML456 training...")
    
    output_dir = Path(output_dir)
    baseline_dir = output_dir / "baseline"
    damaged_dir = output_dir / "damaged"
    
    # Clean and recreate directories
    if output_dir.exists():
        shutil.rmtree(output_dir)
    
    baseline_dir.mkdir(parents=True)
    damaged_dir.mkdir(parents=True)
    
    # Extract zip
    extract_dir = Path("/tmp/ml_training_data_12gate")
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    print(f"  Extracted to: {extract_dir}")
    
    # Organize files
    baseline_count = 0
    damaged_scenarios = {}
    
    for folder in extract_dir.iterdir():
        if not folder.is_dir():
            continue
        
        folder_name = folder.name
        csv_files = list(folder.glob("*.csv"))
        
        print(f"  Found folder: {folder_name} ({len(csv_files)} files)")
        
        if "baseline" in folder_name.lower():
            # Copy baseline files
            for csv_file in csv_files:
                dest = baseline_dir / csv_file.name
                shutil.copy2(csv_file, dest)
                baseline_count += 1
        else:
            # Track damaged scenarios
            scenario_name = folder_name.replace(" ", "_")
            if scenario_name not in damaged_scenarios:
                damaged_scenarios[scenario_name] = 0
            
            # Copy damaged files with scenario prefix
            for csv_file in csv_files:
                dest = damaged_dir / f"{scenario_name}_{csv_file.name}"
                shutil.copy2(csv_file, dest)
                damaged_scenarios[scenario_name] += 1
    
    total_damaged = sum(damaged_scenarios.values())
    
    print(f"\n✅ Data organized:")
    print(f"   Baseline: {baseline_count} files → {baseline_dir}")
    print(f"   Damaged: {total_damaged} files → {damaged_dir}")
    for scenario, count in damaged_scenarios.items():
        print(f"     - {scenario}: {count} files")
    
    return baseline_dir, damaged_dir, baseline_count, total_damaged

def train_ml456_models(baseline_dir, damaged_dir):
    """Train ML456 advanced models."""
    print("\n🤖 Training ML456 Advanced Models...")
    
    try:
        # Change to ml456_advanced directory for training
        original_dir = os.getcwd()
        os.chdir(ml456_path)
        
        # Import training script
        from training.train_advanced_model import main as train_main
        
        # Create config for training
        config = {
            'data': {
                'baseline_dir': str(baseline_dir),
                'damaged_dir': str(damaged_dir),
                'sampling_rate': 100  # Hz - adjust if different
            },
            'model': {
                'type': 'random_forest',
                'n_estimators': 100,
                'max_depth': None
            },
            'training': {
                'test_size': 0.2,
                'random_state': 42
            }
        }
        
        # Save config
        config_path = ml456_path / 'config' / 'training_12gate.yaml'
        config_path.parent.mkdir(exist_ok=True)
        
        import yaml
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        print(f"  Config saved to: {config_path}")
        
        # Run training
        print("\n  Starting training process...")
        print("  This may take several minutes...")
        
        # Call the training script with our data paths
        sys.argv = [
            'train_advanced_model.py',
            '--baseline-dir', str(baseline_dir),
            '--damaged-dir', str(damaged_dir),
            '--output-dir', str(ml456_path / 'checkpoints' / 'advanced'),
        ]
        
        try:
            train_main()
        except SystemExit:
            pass  # Training script may call sys.exit
        
        # Return to original directory
        os.chdir(original_dir)
        
        # Check if models were created
        model_path = ml456_path / 'checkpoints' / 'advanced' / 'random_forest_model.pkl'
        feature_path = ml456_path / 'data' / 'processed' / 'feature_extractor.pkl'
        
        if model_path.exists():
            print(f"\n✅ Model trained successfully!")
            print(f"   Model: {model_path}")
            print(f"   Size: {model_path.stat().st_size / 1024:.1f} KB")
        else:
            print(f"\n⚠️  Model file not found at expected location: {model_path}")
        
        if feature_path.exists():
            print(f"   Feature extractor: {feature_path}")
        else:
            print(f"   ⚠️  Feature extractor not found: {feature_path}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure ml456_advanced dependencies are installed:")
        print("   cd /home/itachi/ml456_advanced")
        print("   pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        os.chdir(original_dir)

def main():
    print("=" * 70)
    print("🏗️  ML456 ADVANCED MODEL TRAINING - 12 Gate Data")
    print("=" * 70)
    
    zip_path = "/home/itachi/ml098/aaja ko final data 12 gate ko.zip"
    output_dir = ml456_path / "data" / "raw" / "12gate_data"
    
    if not Path(zip_path).exists():
        print(f"❌ Error: Data zip not found at {zip_path}")
        sys.exit(1)
    
    # Step 1: Prepare data
    baseline_dir, damaged_dir, baseline_count, damaged_count = prepare_data_for_ml456(zip_path, output_dir)
    
    # Step 2: Train models
    success = train_ml456_models(baseline_dir, damaged_dir)
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 TRAINING COMPLETE!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Rebuild Docker backend:")
        print("   cd /mnt/storage/structural-repair-web")
        print("   sudo docker compose build backend")
        print("\n2. Restart services:")
        print("   sudo docker compose up -d")
        print("\n3. Test ML Baseline Prediction in the UI")
        print("   - Upload a damaged file")
        print("   - Click 'Predict Baseline with ML'")
        print("   - The new trained model will be used!")
    else:
        print("\n⚠️  Training encountered errors. Please check the logs above.")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
