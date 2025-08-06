"""
Import utilities to avoid sys.path.append() hacks
"""
import os
import sys
from pathlib import Path

def setup_project_imports():
    """Add the project root to Python path - call this at the top of your scripts"""
    # Get the current file's directory
    current_file = Path(__file__).resolve()
    
    # Navigate to project root (3 levels up from src/utils/)
    project_root = current_file.parent.parent.parent
    
    # Add to sys.path if not already there
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        print(f"Added {project_root} to Python path")

# Alternative: Auto-setup when imported
def auto_setup():
    """Automatically setup imports when this module is imported"""
    setup_project_imports() 