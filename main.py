#!/usr/bin/env python3
"""CycleNest - Menstrual Cycle Tracking & Predictive Analytics Suite for Desktop Console.
Run with: python main.py
"""

import sys
from pathlib import Path

# Force UTF-8 encoding on Windows consoles
if sys.platform == "win32":
    try:
        if sys.stdout:
            sys.stdout.reconfigure(encoding="utf-8")
        if sys.stderr:
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from cyclenest.main import main

if __name__ == "__main__":
    main()
