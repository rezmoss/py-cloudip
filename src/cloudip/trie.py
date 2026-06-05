"""A binary (Patricia-style) trie over CIDR prefixes for longest-prefix matching.

Separate tries are kept for IPv4 (32-bit) and IPv6 (128-bit) addresses. ``lookup``
descends the trie bit by bit, remembering the most specific (longest-prefix)
range seen along the path — matching the behaviour of go-cloudip / js-cloudip.
"""

from __future__ import annotations

import ipaddress
from typing import Optional

from .types import Range


class _Node:
    __slots__ = ("zero", "one", "range")

    def __init__(self) -> None:
        self.zero: Optional[_Node] = None
        self.one: Optional[_Node] = None
        self.range: Optional[Range] = None


def _parse_network(cidr: str):
    """Return an ip_network for ``cidr`` (host bits allowed), or None if invalid."""
    try:
        return ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return None


class CIDRTrie:
    def __init__(self) -> None:
        self._v4 = _Node()
        self._v6 = _Node()

    def insert(self, rng: Range) -> None:
        net = _parse_network(rng.cidr)
        if net is None:
            return
        nbits = 32 if net.version == 4 else 128
        value = int(net.network_address)
        root = self._v4 if net.version == 4 else self._v6
        node = root
        for i in range(net.prefixlen):
            bit = (value >> (nbits - 1 - i)) & 1
            if bit:
                child = node.one
                if child is None:
                    child = _Node()
                    node.one = child
            else:
                child = node.zero
                if child is None:
                    child = _Node()
                    node.zero = child
            node = child
        # Keep the first range inserted at a given prefix (stable, like the JS port).
        if node.range is None:
            node.range = rng

    def lookup(self, ip: str) -> Optional[Range]:
        try:
            addr = ipaddress.ip_address(ip)
        except ValueError:
            return None
        nbits = 32 if addr.version == 4 else 128
        value = int(addr)
        node: Optional[_Node] = self._v4 if addr.version == 4 else self._v6
        best = node.range if node else None
        for i in range(nbits):
            if node is None:
                break
            bit = (value >> (nbits - 1 - i)) & 1
            node = node.one if bit else node.zero
            if node is not None and node.range is not None:
                best = node.range
        return best
