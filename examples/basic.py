"""Basic usage of the package-level API (fetches/caches data automatically)."""

import cloudip

print("data version:", cloudip.version(), f"({cloudip.range_count()} ranges)")

for ip in ["52.94.76.1", "34.64.0.1", "1.1.1.1", "127.0.0.1"]:
    r = cloudip.lookup(ip)
    if r.found:
        print(f"{ip:16} -> {r.provider} ({r.region or '-'}, {r.service or '-'})")
    else:
        print(f"{ip:16} -> not a known cloud provider")

print("is_aws(52.94.76.1):", cloudip.is_aws("52.94.76.1"))
print("provider(34.64.0.1):", cloudip.get_provider("34.64.0.1"))
print("cloudflare CIDRs:", len(cloudip.get_ips("cloudflare")))
