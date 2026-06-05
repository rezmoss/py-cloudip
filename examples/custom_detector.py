"""A custom Detector with an explicit cache directory and background auto-update."""

import cloudip

# Cache to ./cache and refresh in the background once a day.
detector = cloudip.new_detector(
    data_dir="./cache",
    auto_update_seconds=24 * 60 * 60,
)
try:
    print(detector.lookup("52.94.76.1").to_dict())
    print("has update:", detector.check_update().has_update)
finally:
    detector.close()
