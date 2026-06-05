"""Air-gapped usage: only the bundled database, never the network."""

from cloudip import embedded

print("bundled version:", embedded.version())
print("data age (days): %.1f" % embedded.age_days())
print("is_aws(52.94.76.1):", embedded.is_aws("52.94.76.1"))
print("provider(34.64.0.1):", embedded.get_provider("34.64.0.1"))
