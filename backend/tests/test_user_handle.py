"""Unit tests for the user_handle validation regex."""
from __future__ import annotations

import re

import pytest

# The same pattern used in app/routes/auth.py
_HANDLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{2,29}$")


@pytest.mark.parametrize(
    "handle, expected",
    [
        # --- valid handles ---
        ("Rambo_99", True),   # mixed case, digit, underscore
        ("rambo", True),       # plain lowercase, 5 chars
        ("abc", True),         # minimum 3 chars
        ("a" * 30, True),      # maximum 30 chars
        ("Hello_World_1", True),
        # --- invalid handles ---
        ("99rambo", False),    # starts with digit
        ("r", False),          # 1 char — too short
        ("ab", False),         # 2 chars — too short
        ("a" * 31, False),     # 31 chars — too long
        ("rambo!", False),     # special char !
        ("rambo space", False),  # contains space
        ("_rambo", False),     # starts with underscore
        ("", False),           # empty string
        ("rambo-99", False),   # hyphen not allowed
        ("rambo.99", False),   # dot not allowed
    ],
)
def test_handle_regex(handle: str, expected: bool) -> None:
    result = bool(_HANDLE_RE.match(handle))
    assert result is expected, f"handle={handle!r}: expected match={expected}, got {result}"
