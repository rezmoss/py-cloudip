"""py-cloudip — fast cloud-provider IP detection.

Detect whether an IP address belongs to AWS, GCP, Azure, Cloudflare,
DigitalOcean, or Oracle Cloud. Data comes from the rezmoss/cloudip-db database
(network fetch with SHA-256 verification, on-disk cache, and an embedded
offline fallback).

Quick start::

    import cloudip
    cloudip.is_aws("52.94.76.1")        # True
    cloudip.get_provider("34.64.0.1")   # "gcp"
    cloudip.lookup("52.94.76.1")        # LookupResult(found=True, provider="aws", ...)
"""

from __future__ import annotations

import threading
from typing import List, Optional, Union

from .constants import (
    PROVIDER_AWS,
    PROVIDER_AZURE,
    PROVIDER_CLOUDFLARE,
    PROVIDER_DIGITALOCEAN,
    PROVIDER_GCP,
    PROVIDER_ORACLE,
)
from .detector import Detector, load_version, new_detector
from .types import (
    CheckUpdateResult,
    Database,
    IPEntry,
    LookupResult,
    Provider,
    Range,
    VersionInfo,
)

__version__ = "0.1.0"

__all__ = [
    "Detector",
    "new_detector",
    "lookup",
    "get_provider",
    "is_cloud_provider",
    "is_aws",
    "is_gcp",
    "is_azure",
    "is_cloudflare",
    "is_digitalocean",
    "is_oracle",
    "get_ips",
    "version",
    "range_count",
    "providers",
    "update",
    "check_update",
    "clear_cache",
    "remote_version",
    "CheckUpdateResult",
    "Database",
    "IPEntry",
    "LookupResult",
    "Provider",
    "Range",
    "VersionInfo",
    "PROVIDER_AWS",
    "PROVIDER_GCP",
    "PROVIDER_AZURE",
    "PROVIDER_CLOUDFLARE",
    "PROVIDER_DIGITALOCEAN",
    "PROVIDER_ORACLE",
]

_default: Optional[Detector] = None
_default_lock = threading.Lock()


def _get_default() -> Detector:
    global _default
    if _default is not None:
        return _default
    with _default_lock:
        if _default is None:
            _default = new_detector()
    return _default


def lookup(ip: str) -> LookupResult:
    return _get_default().lookup(ip)


def get_provider(ip: str) -> Provider:
    return _get_default().get_provider(ip)


def is_cloud_provider(ip: str) -> bool:
    return _get_default().is_cloud_provider(ip)


def is_aws(ip: str) -> bool:
    return _get_default().is_aws(ip)


def is_gcp(ip: str) -> bool:
    return _get_default().is_gcp(ip)


def is_azure(ip: str) -> bool:
    return _get_default().is_azure(ip)


def is_cloudflare(ip: str) -> bool:
    return _get_default().is_cloudflare(ip)


def is_digitalocean(ip: str) -> bool:
    return _get_default().is_digitalocean(ip)


def is_oracle(ip: str) -> bool:
    return _get_default().is_oracle(ip)


def get_ips(
    providers: Optional[Union[Provider, List[Provider]]] = None
) -> List[IPEntry]:
    return _get_default().get_ips(providers)


def version() -> str:
    return _get_default().version()


def range_count() -> int:
    return _get_default().range_count()


def providers() -> List[Provider]:
    return _get_default().providers()


def update() -> None:
    _get_default().update()


def check_update() -> CheckUpdateResult:
    return _get_default().check_update()


def remote_version(version_url: Optional[str] = None) -> VersionInfo:
    if version_url is None:
        from .constants import DEFAULT_VERSION_URL

        version_url = DEFAULT_VERSION_URL
    return load_version(version_url)


def clear_cache() -> None:
    global _default
    if _default is not None:
        _default.clear_cache()
        _default.close()
    _default = None
