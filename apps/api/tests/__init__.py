"""Test package init.

Sets ``sys.path`` so the ``app`` package resolves when tests are run via
``unittest discover`` or ``pytest`` regardless of the caller's cwd.
"""

from __future__ import annotations

import sys
from pathlib import Path

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))
