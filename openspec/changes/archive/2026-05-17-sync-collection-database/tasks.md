## 1. Database Setup

- [x] 1.1 Create `db/` module with `__init__.py` and `database.py` containing `init_db()` function that creates SQLite database at `data/now-spinning.db` with tables: `stylus`, `record`, `status`
- [x] 1.2 Add `get_last_sync_date()` function to return the last successful sync date from the `status` table (returns `None` if never synced)
- [x] 1.3 Add `upsert_styli(styli_list)` function — insert-only: skip styli whose ID already exists
- [x] 1.4 Add `upsert_records(records_list)` function — insert new records, update existing ones if data changed
- [x] 1.5 Add `update_sync_date()` function to set `updated_at` in the `status` table to the current date

## 2. Git Sync Module

- [x] 2.1 Create `sync/` module with `__init__.py` and `git_sync.py` containing `clone_or_pull(repo_url, target_dir)` function using `subprocess` to clone or pull
- [x] 2.2 Create `sync/data_extractor.py` with `extract_data(repo_dir)` function that reads `data/styli.json`, `data/collection.json`, and `albums/*.json` and returns parsed styli and records lists
- [x] 2.3 Add `copy_images(repo_dir, dest_dir)` function in `sync/data_extractor.py` that copies all `images/*.jpeg` from the repo to `ui/images/`

## 3. Sync API Endpoint

- [x] 3.1 Add `POST /sync` endpoint in `api/main.py` that returns an SSE stream with status events for each sync step
- [x] 3.2 Implement sync orchestration: show last sync date → clone/pull repo → extract and upsert data → update sync date → report complete/error
- [x] 3.3 Remove stub endpoints `POST /records/sync` and `POST /styli/sync`

## 4. UI Sync View Wiring

- [x] 4.1 Update `renderSync()` to fetch last sync date via `GET /sync/status` (or from initial SSE event) and display "Last updated YYYY/MM/DD" or "Last updated never"
- [x] 4.2 Wire Sync button click to `POST /sync`, consume SSE stream, and update `#sync-status` text with each step status in real-time
- [x] 4.3 Ensure only one status line is displayed at a time during the sync process
