## Why

Stylus navigation currently changes only the displayed item, while usage tracking keeps a different, implicit selection. Persisting a single selection and guarding changes during playback keeps wear totals attached to the stylus actually in use. An offline deletion command also lets owners remove unused local entries safely.

## What Changes

- Normalize existing active flags to one saved selection without changing metadata or hours; preserve that selection during collection sync.
- Expose `active` in stylus data and add a persistent activation endpoint, serialized with playback transitions and rejected during playback.
- Flush previous pending usage before switching, then load the new total and clear the playback baseline.
- Connect Prev/Next to saved selection with stable ordering, wraparound, playback and pending guards, accessible errors, and recovery after uncertain network outcomes.
- Add offline `stylus-hours delete <id>` with transactional active-selection protection and commit-before-success reporting.
- Update help and README, including the stopped-app procedure and local-only deletion behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ui-app`: Persist navigation, initialize from saved selection, update both bars, and handle guarded or failed requests.
- `api-server`: Expose active flags and guarded JSON activation responses.
- `sync-database`: Normalize and persist selection, preserve it during sync, and transactionally reject active deletion.
- `stylus-hours-tracking`: Serialize selection with playback, flush pending usage, and switch tracking without cross-counting.
- `stylus-hours-cli`: Delete inactive local styli with standard-library-only execution and clear offline instructions.

## Impact

Changes affect the existing SQLite helpers, stylus tracker, Flask endpoints, stylus model/mock data, vanilla JavaScript UI, CLI, documentation, and Python/JavaScript tests. The database schema, UI design, and `stylus_hours` event format remain in use. No new runtime dependencies are required. This change stays open; main specs are neither synced nor archived.
