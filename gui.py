#!/usr/bin/env python3
"""CycleNest GUI Launcher - Desktop Graphical Application.
Run with: python gui.py
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from cyclenest.gui.app import launch_gui

if __name__ == "__main__":
    launch_gui()
