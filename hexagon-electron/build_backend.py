#!/usr/bin/env python3
"""
HEXAGON Backend Builder
Packages Python backend with PyInstaller including all ML models
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent / "backend"
ML_MODELS_DIR = BACKEND_DIR / "ml_models"
ML456_DIR = Path.home() / "ml456_advanced"
OUTPUT_DIR = SCRIPT_DIR / "backend-dist"

print("=" * 80)
print("HEXAGON Backend Builder")
print("=" * 80)

def check_dependencies():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller found: {PyInstaller.__version__}")
    except ImportError:
        print("[X] PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")

def collect_ml_models():
    """Collect all ML model files"""
    print("\n[1/5] Collecting ML models...")
    
    models = []
    
    # Main ML models
    if ML_MODELS_DIR.exists():
        for file in ML_MODELS_DIR.rglob("*"):
            if file.is_file() and file.suffix in ['.pkl', '.pth', '.h5', '.json', '.joblib', '.py']:
                models.append(file)
                print(f"  [OK] {file.relative_to(BACKEND_DIR)}")
    
    # ML456 external models
    if ML456_DIR.exists():
        print(f"\n  Collecting ML456 models from {ML456_DIR}")
        for file in ML456_DIR.rglob("*"):
            if file.is_file() and file.suffix in ['.pkl', '.pth', '.h5', '.json', '.joblib']:
                models.append(file)
                print(f"  [OK] {file.name}")
    else:
        print(f"  [WARNING] ML456 directory not found: {ML456_DIR}")
        print(f"  Continuing without ML456...")
    
    print(f"\n  Total models collected: {len(models)}")
    return models

def create_pyinstaller_spec(ml_models):
    """Create PyInstaller spec file"""
    print("\n[2/5] Creating PyInstaller spec...")
    
    # Build data files list
    datas = []
    
    # ML models
    for model in ml_models:
        if ML_MODELS_DIR in model.parents:
            rel_path = model.relative_to(ML_MODELS_DIR)
            datas.append((str(model), str(Path('ml_models') / rel_path.parent)))
        elif ML456_DIR.exists() and ML456_DIR in model.parents:
            rel_path = model.relative_to(ML456_DIR)
            datas.append((str(model), str(Path('ml456_advanced') / rel_path.parent)))
    
    # Backend templates and static files
    backend_extras = [
        (BACKEND_DIR / "templates", "templates"),
        (BACKEND_DIR / "static", "static"),
    ]
    
    for src, dst in backend_extras:
        if src.exists():
            datas.append((str(src), dst))
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

BACKEND_DIR = Path(r'{str(BACKEND_DIR)}')

block_cipher = None

a = Analysis(
    [str(BACKEND_DIR / 'app.py')],
    pathex=[str(BACKEND_DIR), str(BACKEND_DIR / 'services')],
    binaries=[],
    datas={datas},
    hiddenimports=[
        'fastapi',
        'fastapi.responses',
        'fastapi.middleware',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'starlette',
        'starlette.applications',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.routing',
        'starlette.responses',
        'starlette.requests',
        'pydantic',
        'pydantic.main',
        'pydantic.fields',
        'pydantic_core',
        'numpy',
        'pandas',
        'scipy',
        'scikit-learn',
        'sklearn',
        'sklearn.ensemble',
        'sklearn.neighbors',
        'sklearn.tree',
        'sklearn.utils',
        'joblib',
        'torch',
        'matplotlib',
        'PIL',
        'jinja2',
        'typing_extensions',
        'anyio',
        'sniffio',
        'h11',
        'click',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='backend',
)
"""
    
    spec_file = SCRIPT_DIR / "backend.spec"
    spec_file.write_text(spec_content)
    print(f"  [OK] Spec file created: {spec_file}")
    return spec_file

def build_backend(spec_file):
    """Run PyInstaller"""
    print("\n[3/5] Building backend with PyInstaller...")
    print("  This may take several minutes...")
    
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        str(spec_file)
    ]
    
    print(f"  Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=SCRIPT_DIR)
    
    if result.returncode != 0:
        print("  [X] Build failed!")
        sys.exit(1)
    
    print("  [OK] Backend built successfully")

def copy_to_output():
    """Copy build to output directory"""
    print("\n[4/5] Copying to output directory...")
    
    dist_dir = SCRIPT_DIR / "dist" / "backend"
    
    if not dist_dir.exists():
        print(f"  [X] Build directory not found: {dist_dir}")
        sys.exit(1)
    
    # Remove old output
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    
    # Copy new build
    shutil.copytree(dist_dir, OUTPUT_DIR)
    print(f"  [OK] Copied to: {OUTPUT_DIR}")
    
    # Verify executable (platform-specific)
    import platform
    exe_name = "backend.exe" if platform.system() == "Windows" else "backend"
    exe_path = OUTPUT_DIR / exe_name
    if exe_path.exists():
        if platform.system() != "Windows":
            os.chmod(exe_path, 0o755)
        print(f"  [OK] Backend executable ready: {exe_path}")
    else:
        print(f"  [X] Executable not found: {exe_path}")
        sys.exit(1)

def cleanup():
    """Clean up temporary files"""
    print("\n[5/5] Cleaning up...")
    
    to_remove = [
        SCRIPT_DIR / "build",
        SCRIPT_DIR / "dist",
        SCRIPT_DIR / "backend.spec",
    ]
    
    for item in to_remove:
        if item.exists():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            print(f"  [OK] Removed: {item.name}")

def main():
    """Main build process"""
    
    # Verify backend exists
    if not BACKEND_DIR.exists():
        print(f"[X] Backend directory not found: {BACKEND_DIR}")
        sys.exit(1)
    
    print(f"[OK] Backend directory: {BACKEND_DIR}")
    
    try:
        check_dependencies()
        ml_models = collect_ml_models()
        spec_file = create_pyinstaller_spec(ml_models)
        build_backend(spec_file)
        copy_to_output()
        cleanup()
        
        print("\n" + "=" * 80)
        print("[OK] Backend build complete!")
        print("=" * 80)
        print(f"\nBackend ready at: {OUTPUT_DIR}")
        print(f"Executable: {OUTPUT_DIR / 'backend'}")
        print(f"\nTotal size: ~{sum(f.stat().st_size for f in OUTPUT_DIR.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB")
        
    except Exception as e:
        print(f"\n[X] Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
