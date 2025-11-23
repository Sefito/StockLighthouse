"""
Pytest configuration for backend tests.
"""
import sys
from pathlib import Path

# Add both backend and project root to Python path
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent

sys.path.insert(0, str(project_root))
sys.path.insert(0, str(backend_dir))
