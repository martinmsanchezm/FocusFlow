"""
FocusFlow — Entry point.
A Pomodoro-style schedule tracker that shows your current task
as a compact always-on-top overlay synced to the system clock.
"""

import sys
import os

# Ensure the package directory is on the import path when running
# from source or from a PyInstaller bundle.
if getattr(sys, "frozen", False):
    # Running as PyInstaller bundle
    _base = sys._MEIPASS
else:
    _base = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _base)

from app import FocusFlowApp


def main():
    app = FocusFlowApp()
    app.run()


if __name__ == "__main__":
    main()
