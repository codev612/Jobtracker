#!/usr/bin/env python3
"""Job Tracker - Track your job applications."""

import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "gui":
        from jobtracker.gui import run_gui
        run_gui()
    else:
        from jobtracker.cli import main
        main()
