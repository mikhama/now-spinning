## 1. Database

- [x] 1.1 Add a `reset_stylus_hours(stylus_id)` helper in `api/services/db/database.py` that sets `stylus.distance_hours` to `0`
- [x] 1.2 Return `True` from the helper when a stylus row is updated and `False` when no matching row exists

## 2. API

- [x] 2.1 Update `POST /styli/<id>/reset` in `api/main.py` to initialize the database and call `reset_stylus_hours(id)`
- [x] 2.2 Return `{ "success": true }` for existing styli and 404 JSON error for missing styli

## 3. Verification

- [x] 3.1 Add or update backend tests for resetting an existing stylus to `0` in SQLite
- [x] 3.2 Add or update backend tests for resetting a missing stylus returning 404 without changing data
- [x] 3.3 Run the relevant backend test suite or targeted verification commands
