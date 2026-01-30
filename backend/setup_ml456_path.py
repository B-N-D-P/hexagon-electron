"""
This module MUST be imported first to set up sys.path correctly.
Import this before any other backend modules.
"""
import sys
from pathlib import Path

ml456_path = '/home/itachi/ml456_advanced'

# Only add if not already there
if ml456_path not in sys.path:
    # Insert at position 0 to take precedence
    sys.path.insert(0, ml456_path)
    print(f"✓ setup_ml456_path: Added {ml456_path} to sys.path[0]")
