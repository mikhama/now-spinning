## Why

Stylus usage currently updates only as transient runtime/UI state unless a manual reset writes to SQLite. If the Raspberry Pi loses power or the kiosk exits, playback time since the last durable write can be lost, making stylus wear tracking unreliable.

## What Changes

- Track playback time against the active stylus while the backend considers a record playing.
- Persist accumulated stylus hours to SQLite at least every 10 minutes during active playback.
- Flush any pending accumulated stylus hours when playback stops and when the app exits through the kiosk exit path.
- Use SQLite writes that are committed to local disk durability settings appropriate for unexpected shutdown recovery.
- Continue broadcasting `stylus_hours` updates so the existing UI reflects the current in-memory total while persistence happens in the backend.

## Capabilities

### New Capabilities
- `stylus-hours-tracking`: Tracks active stylus playback time, updates live runtime hours, and flushes accumulated hours on interval, stop, and graceful exit.

### Modified Capabilities
- `sync-database`: Add database-level support for incrementing persisted stylus hours and committing stylus-hour writes with durable SQLite settings.
- `api-server`: Ensure the kiosk exit path flushes pending stylus-hour changes before requesting process shutdown.

## Impact

- Affects backend playback status handling, runtime WebSocket event publication, SQLite database helpers, and kiosk/server shutdown handling.
- Uses the existing `stylus.distance_hours` column as the local source of truth for persisted usage.
- No new external dependencies are expected.
