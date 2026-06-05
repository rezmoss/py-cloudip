"""Decompress + msgpack-decode the database, plus hashing helpers."""

from __future__ import annotations

import gzip
import hashlib

import msgpack

from .types import Database, Range


def gunzip(buf: bytes) -> bytes:
    return gzip.decompress(buf)


def sha256_hex(buf: bytes) -> str:
    return hashlib.sha256(buf).hexdigest()


def decode_database(gz_buf: bytes) -> Database:
    """Decode a gzipped MessagePack database into a :class:`Database`."""
    raw = gunzip(gz_buf)
    obj = msgpack.unpackb(raw, raw=False)
    providers = list(obj["providers"])
    ranges = []
    for r in obj["ranges"]:
        idx = r["p"]
        if idx < 0 or idx >= len(providers):
            raise ValueError(f"cloudip: unknown provider index {idx}")
        ranges.append(
            Range(
                cidr=r["cidr"],
                provider=providers[idx],
                region=r.get("r") or None,
                service=r.get("s") or None,
            )
        )
    return Database(
        version=obj.get("version", ""),
        build_time=int(obj.get("build_time", 0)),
        providers=providers,
        ranges=ranges,
    )
