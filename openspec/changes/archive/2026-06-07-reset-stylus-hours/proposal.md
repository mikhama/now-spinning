## Why

The Stylus reset button currently reports success but does not persist the reset to the SQLite database. Users need a reset action to make the stylus start tracking from `0` hours after replacement or maintenance.

## What Changes

- Update `POST /styli/<id>/reset` so it persists the matching stylus with `0` hours in the database.
- Return 404 when the requested stylus does not exist in the database.
- Keep the frontend reset flow using the existing endpoint, with the response reflecting a real persisted reset.

## Capabilities

### New Capabilities

### Modified Capabilities
- `api-server`: `POST /styli/<id>/reset` must persist a database reset instead of returning success without changing storage.
- `sync-database`: The database layer must provide an operation to reset a stylus `distance_hours` value to `0`.

## Impact

- **Backend**: `api/main.py` reset endpoint, `api/services/db/database.py` data access helpers.
- **Data**: Updates existing `stylus.distance_hours` rows in `data/now-spinning.db`.
- **Tests/verification**: Exercise reset for an existing stylus and missing stylus against SQLite-backed data.
