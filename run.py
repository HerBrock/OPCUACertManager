
#!/usr/bin/env python3
"""
Launcher script for OPC UA Certificate Manager.

Run this script from any directory to start the application.

Usage:
    python run.py
"""

import sys
from pathlib import Path

# Get the directory containing this script (project root)
project_root = Path(__file__).resolve().parent

# Add project root to sys.path so 'src' package can be imported
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run the application
from src.ui.main_window import main

if __name__ == "__main__":
    main()
