## Why

The app needs a functional link mode so users can browse their vinyl collection and see which records are not yet linked to NFC tags. Currently the link mode UI shell exists but doesn't properly filter/display unlinked records, has no empty state, and the database stores IDs with leading zeros (e.g. "01" instead of "1") causing mismatches.

## What Changes

- Link mode shows only unlinked records with prev/next navigation
- Empty state when no unlinked records exist (placeholder with "No Unlinked Records" message)
- Link button is out of scope — no wiring needed yet
- API reads records from database instead of mock data, including `linked` field
- Fix ID normalization during sync: strip leading zeros before storing (e.g. "01" → "1")
- Fix album file path resolution during sync: use `data/albums/<release_id>.json`
- Sync pipeline fails loudly on missing files (errors in backend logs, clean "Sync error" on frontend)
- UI re-fetches records/styli after sync completes
- Database schema updated with `linked` column (user deletes DB file manually to apply)

## Capabilities

### New Capabilities
- `link-mode-view`: Link mode UI showing unlinked records with prev/next navigation and empty state

### Modified Capabilities
- `sync-database`: Fix record ID normalization — strip leading zeros during data extraction before DB insert
- `api-server`: Add endpoint or filter to return only unlinked records
- `ui-app`: Link mode rendering updates — empty state, unlinked-only filtering

## Impact

- `api/services/sync/data_extractor.py` — ID stripping, album path fix, error handling with logging
- `api/services/db/database.py` — `linked` column in schema, `get_all_records()` query
- `api/main.py` — `GET /records` reads from DB, sync endpoint logs and reports errors
- `ui/app.js` — Link mode render logic, navigation, empty state, re-fetch after sync
- `ui/index.html` — Link mode empty state HTML
- `data/now-spinning.db` — User deletes manually to apply schema changes
