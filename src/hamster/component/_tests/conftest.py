"""Pytest configuration for component tests.

Imports custom_components.hamster before HA fixtures run. Without this early
import, HA's loader doesn't find the integration even though sys.path is set.
See also: conftest.py (root) for sys.path setup.
"""

from __future__ import annotations

import custom_components.hamster  # noqa: F401
