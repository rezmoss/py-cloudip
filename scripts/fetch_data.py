#!/usr/bin/env python3
"""Refresh the embedded database from cloudip-db.

Downloads ``version.json`` + ``cloudip.msgpack.gz``, verifies the SHA-256 of the
decompressed payload against ``version.json``, and writes both into
``src/cloudip/data/``. Run manually or from the ``sync-data`` workflow.

    python scripts/fetch_data.py
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

BASE = os.environ.get(
    "CLOUDIP_DB_BASE",
    "https://raw.githubusercontent.com/rezmoss/cloudip-db/main/data",
)
OUT_DIR = Path(__file__).resolve().parent.parent / "src" / "cloudip" / "data"


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "py-cloudip-fetch"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    version_json = json.loads(_get(f"{BASE}/version.json").decode("utf-8"))
    gz = _get(f"{BASE}/cloudip.msgpack.gz")

    digest = hashlib.sha256(gzip.decompress(gz)).hexdigest()
    if digest != version_json["sha256"]:
        print(
            f"sha256 mismatch: expected {version_json['sha256']}, got {digest}",
            file=sys.stderr,
        )
        return 1

    (OUT_DIR / "cloudip.msgpack.gz").write_bytes(gz)
    (OUT_DIR / "version.json").write_text(json.dumps(version_json, indent=2) + "\n")

    print(
        f"fetched cloudip-db version={version_json['version']} "
        f"ranges={version_json['ranges']} size_gzip={version_json['size_gzip']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
