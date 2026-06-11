from __future__ import annotations

from opencc import OpenCC


_T2S_CONVERTER = OpenCC("t2s")


def to_simplified(text: str) -> str:
    """Convert final user-visible text to Simplified Chinese."""
    return _T2S_CONVERTER.convert(text or "")
