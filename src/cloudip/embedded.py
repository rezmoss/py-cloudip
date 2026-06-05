"""Offline-only entry point: uses the bundled database and never touches the network.

Mirrors :mod:`cloudip` but the default detector is created with ``offline=True``
and no on-disk cache, so it works in air-gapped environments::

    from cloudip import embedded
    embedded.is_aws("52.94.76.1")   # uses bundled data only
"""

from __future__ import annotations

import threading
import time
from typing import List, Optional, Union

from .detector import Detector, new_detector
from .types import IPEntry, LookupResult, Provider

_default: Optional[Detector] = None
_default_lock = threading.Lock()


def _get_default() -> Detector:
    global _default
    if _default is not None:
        return _default
    with _default_lock:
        if _default is None:
            _default = new_detector(offline=True, data_dir=None)
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


def age_days() -> float:
    """Age of the bundled data in days, based on its build time."""
    d = _get_default()
    return (time.time() - d.build_time()) / 86400
