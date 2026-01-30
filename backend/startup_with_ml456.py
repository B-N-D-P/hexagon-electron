"""
Startup script that properly initializes sys.path for ML456 Advanced integration.
This must be run BEFORE importing app.py to avoid module conflicts.
"""
import sys
import os
from pathlib import Path

# CRITICAL: Add ml456_advanced to path FIRST, before any other imports
ml456_path = '/home/itachi/ml456_advanced'
backend_path = str(Path(__file__).parent.resolve())

# Ensure ml456 is first, then backend
if ml456_path not in sys.path:
    sys.path.insert(0, ml456_path)
if backend_path not in sys.path:
    sys.path.insert(1, backend_path)

# Also set PYTHONPATH environment variable so child processes inherit it
current_pythonpath = os.environ.get('PYTHONPATH', '')
new_pythonpath = f"{ml456_path}:{backend_path}"
if current_pythonpath:
    new_pythonpath += f":{current_pythonpath}"
os.environ['PYTHONPATH'] = new_pythonpath

print(f"✓ Added {ml456_path} to sys.path (position 0)")
print(f"✓ Added {backend_path} to sys.path (position 1)")
print(f"✓ Set PYTHONPATH={new_pythonpath}")

# Now import and run the app
if __name__ == "__main__":
    import uvicorn
    
    # Import app after path is configured
    from app import app
    
    print("\n" + "="*80)
    print("Starting backend with ML456 Advanced integration")
    print("="*80 + "\n")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False  # Disable reload to prevent path issues
    )
