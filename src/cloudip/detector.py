"""The Detector: loads data (network -> cache -> embedded) and answers lookups."""

from __future__ import annotations

import threading
from typing import Dict, List, Optional, Union

from .cache import (
    cache_age_seconds,
    clear_cache,
    read_cache,
    resolve_cache_dir,
    write_cache,
)
from .constants import (
    DEFAULT_DATA_URL,
    DEFAULT_TTL_SECONDS,
    DEFAULT_VERSION_URL,
    HOUR_SECONDS,
    PROVIDER_AWS,
    PROVIDER_AZURE,
    PROVIDER_CLOUDFLARE,
    PROVIDER_DIGITALOCEAN,
    PROVIDER_GCP,
    PROVIDER_ORACLE,
)
from .decode import decode_database
from .embedded_loader import load_embedded_gz
from .source import fetch_data, fetch_version
from .trie import CIDRTrie
from .types import (
    CheckUpdateResult,
    Database,
    IPEntry,
    LookupResult,
    Provider,
    VersionInfo,
)

# Sentinel distinguishing "use default cache dir" from "caching disabled" (None).
_DEFAULT_DIR = ""


class _State:
    __slots__ = ("db", "trie", "by_provider")

    def __init__(self, db: Database, trie: CIDRTrie, by_provider: Dict[str, List[IPEntry]]):
        self.db = db
        self.trie = trie
        self.by_provider = by_provider


def _build_state(db: Database) -> _State:
    trie = CIDRTrie()
    by_provider: Dict[str, List[IPEntry]] = {}
    for r in db.ranges:
        trie.insert(r)
        key = r.provider.lower()
        entry = IPEntry(
            ip_address=r.cidr,
            ip_type="ipv6" if ":" in r.cidr else "ipv4",
            provider=r.provider,
            region=r.region,
            service=r.service,
        )
        by_provider.setdefault(key, []).append(entry)
    return _State(db, trie, by_provider)


class Detector:
    """Detects which cloud provider (if any) owns a given IP address.

    Create one with :func:`new_detector` (which loads data eagerly), or construct
    directly and call :meth:`ready` before use.
    """

    def __init__(
        self,
        data_dir: Optional[str] = _DEFAULT_DIR,
        auto_update_seconds: float = 0,
        offline: bool = False,
        data_url: str = DEFAULT_DATA_URL,
        version_url: str = DEFAULT_VERSION_URL,
        verify_sha256: bool = True,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        timeout: float = 30.0,
    ) -> None:
        # An auto-update interval under an hour is clamped up to one hour.
        if 0 < auto_update_seconds < HOUR_SECONDS:
            auto_update_seconds = HOUR_SECONDS
        self._data_dir = resolve_cache_dir(data_dir)
        self._auto_update_seconds = auto_update_seconds
        self._offline = offline
        self._data_url = data_url
        self._version_url = version_url
        self._verify_sha256 = verify_sha256
        self._ttl_seconds = ttl_seconds
        self._timeout = timeout

        self._state: Optional[_State] = None
        self._lock = threading.RLock()
        self._stop_event: Optional[threading.Event] = None
        self._timer_thread: Optional[threading.Thread] = None

    # -- lifecycle -------------------------------------------------------

    def ready(self) -> "Detector":
        with self._lock:
            if self._state is not None:
                return self
            self._load_initial()
        if self._auto_update_seconds > 0 and not self._offline:
            self._start_auto_update()
        return self

    def close(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        self._timer_thread = None

    def __enter__(self) -> "Detector":
        return self.ready()

    def __exit__(self, *exc) -> None:
        self.close()

    def _start_auto_update(self) -> None:
        self._stop_event = threading.Event()
        interval = self._auto_update_seconds

        def _run() -> None:
            assert self._stop_event is not None
            while not self._stop_event.wait(interval):
                try:
                    self.update()
                except Exception:
                    pass  # background refresh is best-effort

        self._timer_thread = threading.Thread(
            target=_run, name="cloudip-auto-update", daemon=True
        )
        self._timer_thread.start()

    # -- data loading ----------------------------------------------------

    def _load_initial(self) -> None:
        if not self._offline:
            try:
                fresh = fetch_data(
                    self._data_url,
                    self._version_url,
                    self._verify_sha256,
                    timeout=self._timeout,
                )
                self._state = _build_state(decode_database(fresh.bytes))
                if self._data_dir:
                    write_cache(self._data_dir, fresh.version, fresh.bytes)
                return
            except Exception:
                pass  # fall through to cache / embedded

        if self._data_dir:
            cached = read_cache(self._data_dir)
            if cached:
                age = cache_age_seconds(self._data_dir)
                fresh_enough = age is not None and (
                    self._offline or age <= self._ttl_seconds
                )
                # Use cache regardless of age when nothing else is available;
                # being fresh just lets us skip without warning.
                try:
                    self._state = _build_state(decode_database(cached.bytes))
                    if fresh_enough or True:
                        return
                except Exception:
                    pass

        embedded = load_embedded_gz()
        if embedded is not None:
            self._state = _build_state(decode_database(embedded))
            return

        raise RuntimeError(
            "cloudip: no data available (network failed, no cache, no embedded data)"
        )

    def update(self) -> None:
        if self._offline:
            raise RuntimeError("cloudip: update disabled in offline mode")
        fresh = fetch_data(
            self._data_url,
            self._version_url,
            self._verify_sha256,
            timeout=self._timeout,
        )
        state = _build_state(decode_database(fresh.bytes))
        with self._lock:
            self._state = state
        if self._data_dir:
            write_cache(self._data_dir, fresh.version, fresh.bytes)

    def check_update(self) -> CheckUpdateResult:
        if self._offline:
            raise RuntimeError("cloudip: update check disabled in offline mode")
        info = fetch_version(self._version_url, timeout=self._timeout)
        local = self._state.db.version if self._state else ""
        return CheckUpdateResult(has_update=info.version > local, info=info)

    def clear_cache(self) -> None:
        clear_cache(self._data_dir)

    def _require_state(self) -> _State:
        if self._state is None:
            raise RuntimeError(
                "cloudip: detector not ready — call detector.ready() first"
            )
        return self._state

    # -- queries ---------------------------------------------------------

    def lookup(self, ip: str) -> LookupResult:
        r = self._require_state().trie.lookup(ip)
        if r is None:
            return LookupResult(found=False)
        return LookupResult(
            found=True,
            provider=r.provider,
            cidr=r.cidr,
            ip_type="ipv6" if ":" in r.cidr else "ipv4",
            region=r.region,
            service=r.service,
        )

    def get_provider(self, ip: str) -> Provider:
        return self.lookup(ip).provider or ""

    def is_cloud_provider(self, ip: str) -> bool:
        return self.lookup(ip).found

    def is_aws(self, ip: str) -> bool:
        return self.get_provider(ip) == PROVIDER_AWS

    def is_gcp(self, ip: str) -> bool:
        return self.get_provider(ip) == PROVIDER_GCP

    def is_azure(self, ip: str) -> bool:
        return self.get_provider(ip) == PROVIDER_AZURE

    def is_cloudflare(self, ip: str) -> bool:
        return self.get_provider(ip) == PROVIDER_CLOUDFLARE

    def is_digitalocean(self, ip: str) -> bool:
        return self.get_provider(ip) == PROVIDER_DIGITALOCEAN

    def is_oracle(self, ip: str) -> bool:
        return self.get_provider(ip) == PROVIDER_ORACLE

    def get_ips(
        self, providers: Optional[Union[Provider, List[Provider]]] = None
    ) -> List[IPEntry]:
        s = self._require_state()
        if providers is None:
            out: List[IPEntry] = []
            for arr in s.by_provider.values():
                out.extend(arr)
            return out
        want = [providers] if isinstance(providers, str) else list(providers)
        out = []
        for p in want:
            hit = s.by_provider.get(p.lower())
            if hit:
                out.extend(hit)
        return out

    def version(self) -> str:
        return self._state.db.version if self._state else ""

    def build_time(self) -> int:
        return self._state.db.build_time if self._state else 0

    def range_count(self) -> int:
        return len(self._state.db.ranges) if self._state else 0

    def providers(self) -> List[Provider]:
        return list(self._state.db.providers) if self._state else []


def new_detector(**options) -> Detector:
    """Construct a :class:`Detector` and load its data eagerly."""
    return Detector(**options).ready()


def load_version(
    version_url: str = DEFAULT_VERSION_URL, timeout: float = 30.0
) -> VersionInfo:
    return fetch_version(version_url, timeout=timeout)
