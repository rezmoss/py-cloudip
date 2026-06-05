"""Command-line interface: ``cloudip <command> [args]``."""

from __future__ import annotations

import json
import sys
from typing import List

from . import (
    check_update,
    clear_cache,
    get_ips,
    get_provider,
    lookup,
    providers,
    range_count,
    update,
    version,
)

HELP = """cloudip — cloud provider IP utilities (py-cloudip)

Usage:
  cloudip lookup <ip>                Reverse-lookup an IP address
  cloudip get <provider>[,...]       Print CIDRs for one or more providers
  cloudip provider <ip>              Print provider name for an IP
  cloudip providers                  List supported providers
  cloudip version                    Print local data version + range count
  cloudip check-update               Check if a newer upstream version exists
  cloudip update                     Force a refresh from cloudip-db
  cloudip clear-cache                Delete the local cache
  cloudip help                       Show this help

Data source: rezmoss/cloudip-db
"""


def main(argv: List[str] = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cmd = argv[0] if argv else None
    args = argv[1:]

    if cmd in (None, "help", "-h", "--help"):
        sys.stdout.write(HELP)
        return 0

    try:
        if cmd == "lookup":
            if not args:
                raise ValueError("usage: cloudip lookup <ip>")
            r = lookup(args[0])
            print(json.dumps(r.to_dict(), indent=2))
            return 0 if r.found else 1

        if cmd == "provider":
            if not args:
                raise ValueError("usage: cloudip provider <ip>")
            p = get_provider(args[0])
            if not p:
                print("unknown")
                return 1
            print(p)
            return 0

        if cmd == "get":
            if not args:
                raise ValueError("usage: cloudip get <provider>[,<provider>]")
            want = [s.strip() for s in args[0].split(",") if s.strip()]
            for e in get_ips(want):
                print(e.ip_address)
            return 0

        if cmd == "providers":
            for p in providers():
                print(p)
            return 0

        if cmd == "version":
            print(f"{version()} ({range_count()} ranges)")
            return 0

        if cmd == "check-update":
            result = check_update()
            print(json.dumps(result.to_dict(), indent=2))
            return 0 if result.has_update else 1

        if cmd == "update":
            update()
            print("updated")
            return 0

        if cmd == "clear-cache":
            clear_cache()
            print("cache cleared")
            return 0

        sys.stderr.write(f"unknown command: {cmd}\n{HELP}")
        return 2
    except Exception as err:  # noqa: BLE001
        sys.stderr.write(f"error: {err}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
