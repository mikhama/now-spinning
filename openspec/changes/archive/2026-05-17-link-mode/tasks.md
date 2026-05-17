## 1. Database Schema & Sync Fix

- [x] 1.1 Add `linked` column (INTEGER DEFAULT 0) to record table in `database.py` and drop+recreate the record table in `init_db()`
- [x] 1.2 Strip leading zeros from record IDs in `data_extractor.py` using `str(int(id_value))`
- [x] 1.3 Delete existing `data/now-spinning.db` so it gets recreated with the new schema

## 2. API Updates

- [x] 2.1 Update `GET /records` endpoint in `api/main.py` to read records from the database instead of mock data, including the `linked` field
- [x] 2.2 Ensure `cover_image` path is derived from record ID when building Record model from DB rows

## 3. UI — Link Mode View

- [x] 3.1 Add `getUnlinkedRecords()` helper in `app.js` that filters `state.records` to only `linked === false`
- [x] 3.2 Update `getLinkRecord()` to use unlinked records subset instead of all records
- [x] 3.3 Add empty state HTML to link mode section in `index.html` (cover placeholder with "No Unlinked Records" text)
- [x] 3.4 Update `renderLink()` to show empty state when no unlinked records exist, hide record grid
- [x] 3.5 Update link mode action bar logic in `render()` to show standby actions (Mode button only) when no unlinked records
- [x] 3.6 Verify prev/next navigation works within unlinked records only
