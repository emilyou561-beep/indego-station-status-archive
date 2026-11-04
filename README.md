# Indego station status archive

Every 15 minutes, a GitHub Action saves how many bikes (classic and electric) and open docks each Indego station in Philadelphia has, from the system's public [GBFS feed](https://gbfs.bcycle.com/bcycle_indego/gbfs.json).

The public trip files only show rides that happened. They can't show the rides that *didn't* happen because a station was empty or full. This archive is what lets me estimate that lost demand in [indego-bike-share-analysis](https://github.com/emilyou561-beep/indego-bike-share-analysis).

## Files

```text
collect.py                      fetches one snapshot, appends it to today's file
.github/workflows/collect.yml   runs collect.py every 15 min and commits the result
data/station_status/YYYY-MM-DD.csv   one row per station per snapshot (UTC)
data/station_information.csv         station names and coordinates
```

## Columns (`station_status`)

| column | meaning |
|---|---|
| `snapshot_utc` | when the feed was generated |
| `station_id` | Indego station number (matches `start_station` in the trip files) |
| `bikes` / `classic` / `electric` | bikes available to rent |
| `docks` | empty docks available for returns |
| `is_installed`, `is_renting`, `is_returning` | station status flags |
| `last_reported_utc` | last time the station itself checked in |

## Notes

- GitHub's scheduler is best effort, so gaps of 20 to 30 minutes happen, especially at the top of the hour.
- Started November 2026. Earlier history isn't available from the feed.
- Data comes from Indego / BCycle's public feed and belongs to them. This repo just keeps a history of it.
