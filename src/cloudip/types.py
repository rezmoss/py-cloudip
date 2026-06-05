"""Typed data structures used across the library."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

Provider = str


@dataclass(frozen=True)
class Range:
    """A single CIDR block belonging to a provider."""

    cidr: str
    provider: Provider
    region: Optional[str] = None
    service: Optional[str] = None


@dataclass
class IPEntry:
    """A forward-lookup entry returned by ``get_ips``."""

    ip_address: str
    ip_type: str  # "ipv4" | "ipv6"
    provider: Provider
    region: Optional[str] = None
    service: Optional[str] = None

    def to_dict(self) -> dict:
        out = {
            "ip_address": self.ip_address,
            "ip_type": self.ip_type,
            "provider": self.provider,
        }
        if self.region:
            out["region"] = self.region
        if self.service:
            out["service"] = self.service
        return out


@dataclass
class LookupResult:
    """The result of a reverse lookup of an IP address."""

    found: bool
    provider: Optional[Provider] = None
    region: Optional[str] = None
    service: Optional[str] = None
    cidr: Optional[str] = None
    ip_type: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialise omitting absent fields, mirroring js-cloudip's JSON output."""
        if not self.found:
            return {"found": False}
        out = {
            "found": True,
            "provider": self.provider,
            "cidr": self.cidr,
            "ip_type": self.ip_type,
        }
        if self.region:
            out["region"] = self.region
        if self.service:
            out["service"] = self.service
        return out


@dataclass
class VersionInfo:
    """Contents of cloudip-db's ``version.json``."""

    version: str
    build_time: int
    sha256: str
    ranges: int
    size: int
    size_gzip: int

    @classmethod
    def from_dict(cls, d: dict) -> "VersionInfo":
        return cls(
            version=d.get("version", ""),
            build_time=int(d.get("build_time", 0)),
            sha256=d.get("sha256", ""),
            ranges=int(d.get("ranges", 0)),
            size=int(d.get("size", 0)),
            size_gzip=int(d.get("size_gzip", 0)),
        )

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "build_time": self.build_time,
            "sha256": self.sha256,
            "ranges": self.ranges,
            "size": self.size,
            "size_gzip": self.size_gzip,
        }


@dataclass
class Database:
    """The decoded database."""

    version: str
    build_time: int
    providers: list = field(default_factory=list)
    ranges: list = field(default_factory=list)


@dataclass
class CheckUpdateResult:
    """Result of ``check_update``."""

    has_update: bool
    info: Optional[VersionInfo] = None

    def to_dict(self) -> dict:
        out = {"has_update": self.has_update}
        if self.info is not None:
            out["info"] = self.info.to_dict()
        return out
