## Context

The Now Spinning app currently uses in-memory mock data (`api/mock_data.py`) for records and styli. The sync view exists in the UI with a hardcoded status message and a non-functional Sync button. The user's vinyl collection data lives in the `git@github.com:mikhama/my-musical-journey.git` repository as JSON files.

This design covers the backend sync pipeline that downloads data from Git and persists it to SQLite, plus the UI wiring to show real-time sync progress.

## Goals / Non-Goals

**Goals:**
- Implement a working sync pipeline triggered by the Sync button
- Persist collection data (records, styli) to a local SQLite database
- Show step-by-step status updates in the sync view UI
- Track last successful sync date

**Non-Goals:**
- Replacing mock data reads in other views (standby, play, link, etc.) — deferred to future features
- Authentication or SSH key management for Git
- Conflict resolution — Git repo is the single source of truth

## Decisions

### 1. SQLite via Python stdlib `sqlite3`
Use Python's built-in `sqlite3` module. No ORM needed — the schema is simple (3 tables) and queries are straightforward.

**Alternative**: SQLAlchemy — rejected as over-engineered for 3 simple tables with basic CRUD.

### 2. Git CLI via `subprocess`
Shell out to `git clone` / `git pull` using Python `subprocess`. The Pi already has git installed.

**Alternative**: GitPython library — rejected to avoid an additional dependency for two simple commands.

### 3. Database file location
Store the SQLite database at `data/now-spinning.db` relative to the project root. Create the `data/` directory if it doesn't exist.

### 4. Sync endpoint with SSE (Server-Sent Events) for status updates
Use a single `POST /sync` endpoint that returns SSE stream so the frontend can display real-time status. Each step sends a status event. This replaces the separate `/records/sync` and `/styli/sync` stubs.

**Alternative**: WebSocket — already available via flask-sock, but SSE is simpler for one-way server-to-client status updates and doesn't require keeping a WS connection open.

**Alternative**: Polling — rejected as it requires multiple requests and adds complexity.

### 5. Upsert strategy
- **Styli**: Insert-only. If a stylus ID already exists in the database, skip it (do not update). This preserves any local modifications to stylus data (e.g., hours tracking).
- **Records**: Upsert. If a record ID exists and data has changed, update it. This keeps the collection in sync with the source repo.

### 6. Cover images copied to ui/images/albums/
During Step 2, copy all `images/*.jpeg` from the cloned repo to `ui/images/albums/`. Use `shutil.copy2` to preserve metadata. Overwrite existing files — the repo is the source of truth for images. The `albums/` subdirectory keeps cover art separated from other UI image assets.

### 7. Sync runs in the request thread
The sync pipeline runs synchronously in the request handler. The SSE stream keeps the connection alive while status updates are sent. This is acceptable because only one user operates the device at a time.

### 8. Tmp folder for git repo
Clone/pull the repo to a `tmp/my-musical-journey` folder relative to project root. This folder is gitignored.

### 9. Service modules under api/services/
All new backend modules (`db/`, `sync/`) live under `api/services/` to keep the project organized with backend logic co-located under the `api` package.

### 10. No step number prefixes in status messages
SSE status messages use plain descriptive labels ("Downloading collection", "Updating database") without "Step N:" prefixes, for a cleaner UI.

### 11. Blinking dot sync indicator
While sync is in progress, a blinking dot (`●`) is shown before the status text via a CSS `::before` pseudo-element with a `syncing` class. The dot is removed on "Sync complete" or "Sync error".

## Risks / Trade-offs

- **[Git SSH access]** → The Pi must have SSH keys configured for GitHub access. This is a deployment prerequisite, not handled by the app.
- **[No retry logic]** → If git pull or JSON parsing fails mid-sync, the entire sync reports an error. The database remains in its previous consistent state since upserts are wrapped in a transaction.
- **[Single-threaded sync]** → Only one sync can run at a time. Acceptable for a single-user device.
- **[Database locking]** → SQLite has limited concurrency. Acceptable since only the sync process writes and reads are infrequent.
