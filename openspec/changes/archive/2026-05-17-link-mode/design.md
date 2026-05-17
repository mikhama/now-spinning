## Context

The Now Spinning app has a link mode UI shell that shows records with cover, ID, artist, title, and a linked/not-linked status badge. Currently it iterates over ALL records. The user wants link mode to show only unlinked records, with prev/next navigation, and an empty state when none exist.

Additionally, the sync pipeline stores record IDs as-is from collection.json, which may include leading zeros (e.g. "01"). These need to be normalized to plain integers-as-strings (e.g. "1") since the rest of the system (NFC scan events, API lookups) uses normalized IDs.

## Goals / Non-Goals

**Goals:**
- Link mode browses only unlinked records with prev/next
- Empty state shown when no unlinked records exist
- Record IDs normalized (leading zeros stripped) during sync extraction
- Database recreated to fix existing data with leading zeros

**Non-Goals:**
- Link button functionality (wiring the actual NFC write) — explicitly out of scope
- Re-link mode changes
- Database migrations — DB will simply be recreated

## Decisions

### 1. Filter unlinked records client-side
The `GET /records` endpoint already returns all records with a `linked` field. The UI will filter `state.records` to get unlinked records for link mode navigation, same as it already filters linked records for re-link mode via `getLinkedRecords()`. No new API endpoint needed.

**Rationale:** Keeps the API simple, the record list is small (vinyl collection), and the filter pattern already exists in the codebase (`getLinkedRecords`).

### 2. Add `linked` column to the record table
The database `record` table currently lacks a `linked` column. Add `linked INTEGER DEFAULT 0` to the schema. All records start as unlinked (0). The `GET /records` API will read this from the DB and include it in the response.

**Rationale:** Link status must persist across restarts. SQLite INTEGER works as boolean (0/1).

### 3. Strip leading zeros in data_extractor.py
Convert record ID using `str(int(id_value))` during extraction, before the record dict is built. This normalizes "01" → "1", "001" → "1", etc.

**Rationale:** Fix at the source (extraction) rather than at read time. All downstream code already expects normalized IDs.

### 4. Manual DB deletion for schema changes
The user deletes the `data/now-spinning.db` file manually when schema changes are needed. `init_db()` uses `CREATE TABLE IF NOT EXISTS` and never drops tables automatically — this prevents accidental data loss on every server start.

**Rationale:** Auto-dropping tables in `init_db()` would wipe all records on every restart. Manual deletion is safer and gives the user control.

### 5. Reuse standby not-found pattern for empty state
The empty state in link mode will use the same cover-placeholder pattern as standby's "Record Not Found" but with "No Unlinked Records" text. This maintains visual consistency.

### 6. Sync pipeline fails loudly on missing files
The data extractor raises `FileNotFoundError` when required files are missing (styli.json, collection.json, album files). The sync endpoint catches exceptions, logs full details with traceback to backend logs, and shows a clean "Sync error" message on the frontend without exposing internal paths.

**Rationale:** Silent skipping of missing files caused sync to report success with 0 records — confusing and hard to debug.

### 7. Album file path uses `data/albums/<release_id>.json`
Album data files are located at `data/albums/<release_id>.json` in the repo, not `albums/<album_file>`. The extractor builds the path from `release_id`.

**Rationale:** Matches actual repo structure.

### 8. Re-fetch records after sync
The UI re-fetches records and styli from the API after sync completes or errors. This ensures link mode has current data without requiring a page refresh.

**Rationale:** Without re-fetching, navigating to link mode after sync showed stale (empty) state.

## Risks / Trade-offs

- [Manual DB deletion required for schema changes] → Acceptable pre-production. User must delete DB file and re-sync.
- [Client-side filtering won't scale] → Fine for a personal vinyl collection (typically <500 records).
