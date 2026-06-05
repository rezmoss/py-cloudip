"""On-disk caching of the downloaded database under a user cache directory."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import NamedTuple, Optional

_DATA_FILE = "cloudip.msgpack.gz"
_META_FILE = "version.json"


class CachedData(NamedTuple):
    version: str
    bytes: bytes


def _default_cache_dir() -> str:
    base = (
        os.environ.get("XDG_CACHE_HOME")
        or os.path.join(os.path.expanduser("~"), ".cache")
    )
    return os.path.join(base, "py-cloudip")


def resolve_cache_dir(dir: Optional[str]) -> Optional[str]:
    """``None`` disables caching; an unset (sentinel) value uses the default dir."""
    if dir is None:
        return None
    if dir == "":
        return _default_cache_dir()
    return dir


def read_cache(dir: str) -> Optional[CachedData]:
    try:
        p = Path(dir)
        data = (p / _DATA_FILE).read_bytes()
        meta = json.loads((p / _META_FILE).read_text("utf-8"))
        return CachedData(version=meta.get("version", ""), bytes=data)
    except (OSError, ValueError):
        return None


def write_cache(dir: str, version: str, data: bytes) -> None:
    try:
        p = Path(dir)
        p.mkdir(parents=True, exist_ok=True)
        (p / _DATA_FILE).write_bytes(data)
        (p / _META_FILE).write_text(
            json.dumps({"version": version, "stored_at": time.time()})
        )
    except OSError:
        pass  # best-effort


def cache_age_seconds(dir: str) -> Optional[float]:
    try:
        meta = json.loads((Path(dir) / _META_FILE).read_text("utf-8"))
        return time.time() - float(meta["stored_at"])
    except (OSError, ValueError, KeyError):
        return None


def clear_cache(dir: Optional[str]) -> None:
    resolved = resolve_cache_dir(dir if dir is not None else "")
    if not resolved:
        return
    try:
        shutil.rmtree(resolved, ignore_errors=True)
    except OSError:
        pass
