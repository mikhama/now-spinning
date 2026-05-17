## Why

The sync view currently has a hardcoded placeholder status text and a non-functional Sync button. The app needs a real backend sync pipeline that downloads the user's vinyl collection data from a GitHub repository and persists it to a local SQLite database, replacing the in-memory mock data approach for records and styli.

## What Changes

- Add a `POST /sync` API endpoint that orchestrates a multi-step sync pipeline with real-time status updates
- Step 0: Show last successful sync date (or "never" if first run)
- Step 1: Clone or pull the `git@github.com:mikhama/my-musical-journey.git` repository to a tmp folder
- Step 2: Extract `data/styli.json`, `data/collection.json`, and `albums/*.json` from the repo and upsert into a SQLite database with tables: `stylus`, `record`, `status`. Copy `images/*.jpeg` to `ui/images/albums/`
- Step 3: Report sync complete or sync error
- UI sync view updates status text in real-time as each step progresses, with a blinking dot indicator while sync is in progress
- Status messages use plain labels (e.g., "Downloading collection") without step number prefixes
- Styli with existing IDs are **not** updated (insert-only); records with existing IDs **are** updated if data changed
- Store last successful update date in a `status` table

## Capabilities

### New Capabilities
- `sync-pipeline`: Backend sync orchestration (in `api/services/sync/`) — git clone/pull, JSON extraction, SQLite upsert, status reporting
- `sync-database`: SQLite database schema and data access layer (in `api/services/db/`) for stylus, record, and status tables

### Modified Capabilities
- `sync-view`: Update the sync view to wire up the Sync button to the real backend endpoint and display real-time step statuses

## Impact

- **New dependency**: SQLite (Python stdlib `sqlite3`) — no external packages needed
- **New dependency**: `git` CLI must be available on the host (already present on Raspberry Pi)
- **API**: New `POST /sync` endpoint replacing the stub `POST /records/sync` and `POST /styli/sync`
- **Database**: New SQLite database file created at runtime (e.g., `data/now-spinning.db`)
- **UI**: `renderSync()` function updated to handle real sync flow with status updates
- **Data flow**: This change only populates the database — integration with existing views (replacing mock data reads) is deferred to future features
