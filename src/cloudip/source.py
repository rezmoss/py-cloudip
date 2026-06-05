"""Network fetching of version metadata and the database, with SHA-256 verification."""

from __future__ import annotations

import json
import urllib.request
from typing import NamedTuple, Optional

from .constants import DEFAULT_DATA_URL, DEFAULT_VERSION_URL
from .decode import gunzip, sha256_hex
from .types import VersionInfo

_USER_AGENT = "py-cloudip"


def _get(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        status = getattr(resp, "status", 200)
        if status and status >= 400:
            raise OSError(f"cloudip: HTTP {status} from {url}")
        return resp.read()


def fetch_version(
    version_url: str = DEFAULT_VERSION_URL, timeout: float = 30.0
) -> VersionInfo:
    data = _get(version_url, timeout)
    return VersionInfo.from_dict(json.loads(data.decode("utf-8")))


class FetchedData(NamedTuple):
    bytes: bytes
    version: str


def fetch_data(
    data_url: str = DEFAULT_DATA_URL,
    version_url: str = DEFAULT_VERSION_URL,
    verify_sha256: bool = True,
    verify_against: Optional[VersionInfo] = None,
    timeout: float = 30.0,
) -> FetchedData:
    """Download the gzipped database and verify its SHA-256 against version.json."""
    gz = _get(data_url, timeout)
    info = verify_against
    if info is None and (verify_sha256 or True):
        info = fetch_version(version_url, timeout)
    if verify_sha256:
        raw = gunzip(gz)
        digest = sha256_hex(raw)
        if digest != info.sha256:
            raise ValueError(
                f"cloudip: sha256 mismatch (expected {info.sha256}, got {digest})"
            )
    return FetchedData(bytes=gz, version=info.version if info else "")
