"""Save one snapshot of Indego station status (GBFS) to a daily CSV.

Run on a schedule by .github/workflows/collect.yml. Each run appends one row
per station to data/station_status/YYYY-MM-DD.csv (date in UTC).
"""

import csv
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = os.environ.get("GBFS_BASE", "https://gbfs.bcycle.com/1/bcycle_indego")
OUT_DIR = Path("data/station_status")
INFO_FILE = Path("data/station_information.csv")

FIELDS = [
    "snapshot_utc", "station_id", "bikes", "classic", "electric", "docks",
    "is_installed", "is_renting", "is_returning", "last_reported_utc",
]


def get(feed: str, tries: int = 3) -> dict:
    url = f"{BASE}/{feed}.json"
    for i in range(tries):
        try:
            if url.startswith("file://"):
                return json.loads(Path(url[7:]).read_text())
            req = urllib.request.Request(url, headers={"User-Agent": "indego-station-archive"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:  # network hiccups are common, retry a couple of times
            print(f"{feed}: attempt {i + 1} failed: {e}", file=sys.stderr)
            time.sleep(5)
    raise SystemExit(f"could not fetch {feed}")


def iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def short_id(station_id: str) -> str:
    return station_id.replace("bcycle_indego_", "")


def save_status() -> int:
    feed = get("station_status")
    snap = iso(feed["last_updated"])
    out = OUT_DIR / f"{snap[:10]}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)

    # skip if this exact feed timestamp was already saved (e.g. a retried run)
    if out.exists() and snap in out.read_text()[-5000:]:
        print("snapshot already saved:", snap)
        return 0

    new_file = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.writer(f)
        if new_file:
            w.writerow(FIELDS)
        for s in feed["data"]["stations"]:
            types = s.get("num_bikes_available_types", {})
            w.writerow([
                snap, short_id(s["station_id"]), s["num_bikes_available"],
                types.get("classic", 0) + types.get("smart", 0), types.get("electric", 0),
                s["num_docks_available"], s["is_installed"], s["is_renting"], s["is_returning"],
                iso(s["last_reported"]),
            ])
    n = len(feed["data"]["stations"])
    print(f"{snap}: {n} stations -> {out}")
    return n


def save_info() -> None:
    """Station names and locations. Rewritten each run, so git only records real changes."""
    feed = get("station_information")
    rows = sorted(
        (short_id(s["station_id"]), s["name"], s["lat"], s["lon"], s.get("_bcycle_station_type", ""))
        for s in feed["data"]["stations"]
    )
    INFO_FILE.parent.mkdir(parents=True, exist_ok=True)
    with INFO_FILE.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["station_id", "name", "lat", "lon", "station_type"])
        w.writerows(rows)


if __name__ == "__main__":
    save_status()
    save_info()
