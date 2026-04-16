"""Shared test configuration.

Ensures the ``app`` package can be imported directly from the ``apps/api``
directory regardless of where the test runner is invoked.
"""

from __future__ import annotations

import sys
from pathlib import Path

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))
