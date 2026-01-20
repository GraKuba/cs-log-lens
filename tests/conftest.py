"""
Pytest configuration for CS Log Lens tests

This file ensures that the backend module can be imported from tests.
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
