"""Input validation helpers."""
from __future__ import annotations


def validate_ascii(text: str) -> bool:
    """Return True iff all characters are in ASCII printable range (0x20-0x7E) or newline (0x0A).

    This enforces English-only input by rejecting any non-ASCII characters such as
    Devanagari, Telugu, Arabic, emoji, etc.
    """
    for ch in text:
        cp = ord(ch)
        if cp == 0x0A:  # newline
            continue
        if cp == 0x0D:  # carriage return — allow it alongside newline
            continue
        if 0x20 <= cp <= 0x7E:
            continue
        return False
    return True
