#!/usr/bin/env python3
"""
HEXAGON UI - Setup Verification Script
Checks if all dependencies are installed and system is ready
"""

import sys
import importlib.util

def check_dependency(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        module = importlib.import_module(import_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {package_name:<20} {version}")
        return True
    except ImportError:
        print(f"❌ {package_name:<20} NOT INSTALLED")
        return False

def main():
    """Verify setup"""
    print("=" * 60)
    print("HEXAGON Structural Health - UI Setup Verification")
    print("=" * 60)
    print()
    
    required_packages = [
        ("PyQt5", "PyQt5.QtWidgets"),
        ("NumPy", "numpy"),
        ("SciPy", "scipy"),
        ("pySerial", "serial"),
        ("pyqtgraph", "pyqtgraph"),
    ]
    
    print("Checking dependencies:")
    print("-" * 60)
    
    all_ok = True
    for pkg_name, import_name in required_packages:
        if not check_dependency(pkg_name, import_name):
            all_ok = False
    
    print("-" * 60)
    print()
    
    if all_ok:
        print("✅ All dependencies are installed!")
        print()
        print("You can now run the application:")
        print("  python3 ui_main.py")
        print()
        return 0
    else:
        print("❌ Some dependencies are missing!")
        print()
        print("Install them using:")
        print("  pip install -r ui_requirements.txt")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(main())
