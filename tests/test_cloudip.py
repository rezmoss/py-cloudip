"""Tests run fully offline against the bundled database."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest  # noqa: E402

from cloudip import embedded  # noqa: E402
from cloudip.detector import Detector, new_detector  # noqa: E402
from cloudip.trie import CIDRTrie  # noqa: E402
from cloudip.types import Range  # noqa: E402


@pytest.fixture(scope="module")
def det():
    d = new_detector(offline=True, data_dir=None)
    yield d
    d.close()


def test_trie_longest_prefix():
    t = CIDRTrie()
    t.insert(Range(cidr="10.0.0.0/8", provider="aws"))
    t.insert(Range(cidr="10.1.0.0/16", provider="gcp"))
    assert t.lookup("10.2.3.4").provider == "aws"
    assert t.lookup("10.1.2.3").provider == "gcp"  # more specific wins
    assert t.lookup("11.0.0.1") is None


def test_trie_ipv6():
    t = CIDRTrie()
    t.insert(Range(cidr="2600:1f00::/24", provider="aws"))
    assert t.lookup("2600:1f00::1").provider == "aws"
    assert t.lookup("2700::1") is None


def test_trie_invalid_input():
    t = CIDRTrie()
    t.insert(Range(cidr="not-an-ip", provider="aws"))  # ignored
    assert t.lookup("not-an-ip") is None
    assert t.lookup("999.1.1.1") is None


def test_metadata(det):
    assert det.range_count() > 100_000
    assert set(det.providers()) == {
        "aws",
        "gcp",
        "azure",
        "cloudflare",
        "digitalocean",
        "oracle",
    }
    assert det.version()


def test_lookup_unknown(det):
    r = det.lookup("127.0.0.1")
    assert r.found is False
    assert r.to_dict() == {"found": False}


def test_get_ips_filter(det):
    cf = det.get_ips("cloudflare")
    assert len(cf) > 0
    assert all(e.provider == "cloudflare" for e in cf)
    multi = det.get_ips(["aws", "gcp"])
    assert all(e.provider in ("aws", "gcp") for e in multi)


def test_known_aws_ip(det):
    # 52.94.76.0/22 is AWS us-east-1 in the dataset; this IP lies inside it.
    r = det.lookup("52.94.76.1")
    assert r.found is True
    assert r.provider == "aws"
    assert r.ip_type == "ipv4"
    assert det.is_aws("52.94.76.1") is True
    assert det.is_gcp("52.94.76.1") is False
    assert det.is_cloud_provider("52.94.76.1") is True


def test_provider_helpers_consistent(det):
    sample = det.get_ips("cloudflare")[0]
    network = sample.ip_address
    # pick a host inside the cidr
    import ipaddress

    host = str(next(ipaddress.ip_network(network, strict=False).hosts()))
    assert det.is_cloudflare(host) is True


def test_offline_module():
    assert embedded.range_count() > 100_000
    assert embedded.age_days() >= 0
    assert isinstance(embedded.providers(), list)


def test_offline_update_raises():
    d = new_detector(offline=True, data_dir=None)
    with pytest.raises(RuntimeError):
        d.update()
    with pytest.raises(RuntimeError):
        d.check_update()
    d.close()


def test_context_manager():
    with Detector(offline=True, data_dir=None) as d:
        assert d.range_count() > 0
