# py-cloudip

[![PyPI version](https://img.shields.io/pypi/v/py-cloudip.svg)](https://pypi.org/project/py-cloudip/)
[![Python versions](https://img.shields.io/pypi/pyversions/py-cloudip.svg)](https://pypi.org/project/py-cloudip/)
[![CI](https://github.com/rezmoss/py-cloudip/actions/workflows/ci.yml/badge.svg)](https://github.com/rezmoss/py-cloudip/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/pypi/l/py-cloudip.svg)](https://github.com/rezmoss/py-cloudip/blob/main/LICENSE)

Fast cloud-provider IP detection for Python. Identify whether an IP address
belongs to **AWS, GCP, Azure, Cloudflare, DigitalOcean, or Oracle Cloud** via
longest-prefix-match lookups over a Patricia/binary trie.

A Python port of [js-cloudip](https://github.com/rezmoss/js-cloudip) and
[go-cloudip](https://github.com/rezmoss/go-cloudip), backed by the daily-updated
[cloudip-db](https://github.com/rezmoss/cloudip-db) MessagePack database.

- **Fast** — binary trie, IPv4 + IPv6, longest-prefix match.
- **Auto-updating** — fetches fresh data from `cloudip-db` with SHA-256 verification.
- **Offline-capable** — file cache plus an embedded database bundled in the wheel.
- **Zero config** — works on first call; one tiny dependency (`msgpack`).

## Install

```bash
pip install py-cloudip
```

## Usage

```python
import cloudip

cloudip.is_aws("52.94.76.1")        # True
cloudip.get_provider("34.64.0.1")   # "gcp"
cloudip.is_cloud_provider("1.1.1.1")  # True

r = cloudip.lookup("52.94.76.1")
# LookupResult(found=True, provider="aws", region="us-east-1", service="EC2",
#              cidr="52.94.76.0/22", ip_type="ipv4")
r.to_dict()
# {"found": True, "provider": "aws", "cidr": "52.94.76.0/22",
#  "ip_type": "ipv4", "region": "us-east-1", "service": "EC2"}

# Forward lookup: every CIDR for one or more providers
cloudip.get_ips("cloudflare")        # list[IPEntry]
cloudip.get_ips(["aws", "gcp"])
```

### Provider checks

`is_aws`, `is_gcp`, `is_azure`, `is_cloudflare`, `is_digitalocean`, `is_oracle`,
`is_cloud_provider`.

### Metadata & updates

```python
cloudip.version()        # "2026-06-05"
cloudip.range_count()    # 124455
cloudip.providers()      # ["aws", "gcp", "cloudflare", "azure", "digitalocean", "oracle"]
cloudip.check_update()   # CheckUpdateResult(has_update=..., info=VersionInfo(...))
cloudip.update()         # force refresh
cloudip.clear_cache()
```

## Custom detector

```python
detector = cloudip.new_detector(
    data_dir="./cache",            # None disables file caching; "" = default ~/.cache/py-cloudip
    auto_update_seconds=86400,     # background refresh (min 1h); 0 disables
    offline=False,                 # air-gapped mode
    verify_sha256=True,
    ttl_seconds=86400,
)
detector.lookup("52.94.76.1")
detector.close()                   # stop the background updater
# or: with cloudip.Detector(...) as d: ...
```

## Offline / air-gapped

The `cloudip.embedded` module never touches the network — it uses only the
database bundled in the package:

```python
from cloudip import embedded
embedded.is_aws("52.94.76.1")   # uses bundled data only
embedded.age_days()             # how old the bundled data is
```

## CLI

```bash
cloudip lookup 52.94.76.1
cloudip provider 34.64.0.1
cloudip get cloudflare
cloudip get aws,gcp
cloudip providers
cloudip version
cloudip check-update
cloudip update
cloudip clear-cache
```

(Also runnable as `python -m cloudip`.)

## How it works

1. Fetch `version.json` + `cloudip.msgpack.gz` from `cloudip-db`.
2. Verify the SHA-256 of the decompressed MessagePack against `version.json`.
3. Decode and build per-protocol tries for sub-millisecond lookups.
4. On network failure, fall back to the on-disk cache, then the embedded database.

## License

MIT
