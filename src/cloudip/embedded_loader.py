"""Locate and read the embedded fallback database shipped inside the package."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

_DATA_FILE = "cloudip.msgpack.gz"


def load_embedded_gz() -> Optional[bytes]:
    candidates = [
        Path(__file__).resolve().parent / "data" / _DATA_FILE,
        Path(__file__).resolve().parent / _DATA_FILE,
    ]
    for p in candidates:
        try:
            return p.read_bytes()
        except OSError:
            continue
    # Fall back to importlib.resources for zip/installed layouts.
    try:
        from importlib.resources import files

        res = files("cloudip").joinpath("data", _DATA_FILE)
        return res.read_bytes()
    except (OSError, ModuleNotFoundError, FileNotFoundError, AttributeError):
        return None
