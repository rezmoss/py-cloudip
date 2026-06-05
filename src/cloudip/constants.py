"""Shared constants: provider names, default URLs, and timing defaults."""

PROVIDER_AWS = "aws"
PROVIDER_GCP = "gcp"
PROVIDER_AZURE = "azure"
PROVIDER_CLOUDFLARE = "cloudflare"
PROVIDER_DIGITALOCEAN = "digitalocean"
PROVIDER_ORACLE = "oracle"

DEFAULT_BASE_URL = "https://raw.githubusercontent.com/rezmoss/cloudip-db/main/data"
DEFAULT_DATA_URL = f"{DEFAULT_BASE_URL}/cloudip.msgpack.gz"
DEFAULT_VERSION_URL = f"{DEFAULT_BASE_URL}/version.json"

HOUR_SECONDS = 60 * 60
DEFAULT_TTL_SECONDS = 24 * HOUR_SECONDS
