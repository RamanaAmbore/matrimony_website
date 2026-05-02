"""Settings schemas."""
from __future__ import annotations

from typing import Any

import msgspec


class SettingsUpdateRequest(msgspec.Struct):
    """Partial settings update — keys from the settings table."""
    # We use a dict-like approach via msgspec raw
    pass
