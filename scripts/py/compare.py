"""Helpers for comparing HTML before/after round-trip."""
from __future__ import annotations

import difflib
import hashlib


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def unified_diff(before: str, after: str, name: str) -> str:
    return "".join(
        difflib.unified_diff(
            before.splitlines(keepends=True),
            after.splitlines(keepends=True),
            fromfile=f"{name}.before",
            tofile=f"{name}.after",
            n=3,
        )
    )


def is_fixed_point(before: str, after: str) -> bool:
    return before == after
