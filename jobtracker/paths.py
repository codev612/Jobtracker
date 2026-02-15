"""Application base path - works when running as script or as frozen executable."""

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    BASE_PATH = Path(sys.executable).parent
else:
    BASE_PATH = Path(__file__).parent.parent
