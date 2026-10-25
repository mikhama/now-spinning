## Why

Stylus usage belongs to the local Pi database, but new rows currently import an initial total from the collection repository. Operators need a direct offline way to inspect, correct, or reset that total without editing SQL or depending on the application server.

## What Changes

- Add `./bin/stylus-hours list`, `set <id> <hours>`, and `reset <id>` using Python's built-in SQLite support and the existing `data/now-spinning.db`.
- Share a validated, transactional absolute-total database operation between set and reset, retaining the existing API reset behavior.
- Report previous and new totals after successful changes; reject missing databases, missing styli, invalid hours, and failed saves with a failure status.
- Ignore collection `distance_hours`: initialize new styli at zero and preserve existing local totals.
- Document stopping the app before using the tool, restarting afterward, and seeding initial hours after collection sync on a new Pi. The script has no application lock.

## Capabilities

### New Capabilities

- `stylus-hours-cli`: Offline listing, setting, and resetting of saved stylus hours, including validation, errors, and the stopped-app workflow.

### Modified Capabilities

- `sync-database`: Add an absolute-total operation shared by set/reset and make local stylus hours authoritative during collection sync.

## Impact

Changes affect `bin/`, the shared SQLite database layer, a small standard-library CLI module, regression tests, and README usage instructions. No new dependencies or schema migration are needed. The collection repository can remove `distance_hours` without losing existing Pi totals. OpenSpec delta specs remain in this active change without syncing or archiving.
