## Why

A transient NFC read failure during Standby currently replaces a successfully scanned record with “NFC Reading Error.” NFC polling runs only in Standby. The error should be visible only before the program has read a record successfully; later failures should leave the last resolved scan on screen.

## What Changes

- Emit the NFC reading error at most once during startup, before the first successful tag read. Keep polling through no-card and read-error results so the first successful scan can recover the display.
- Keep the last resolved Standby view when a later hardware read error occurs, preserving its record and selected side. Ignore externally supplied null scan events during Playing so they leave playback state unchanged.
- Keep the last successful scan in the server's reconnect state when a later externally supplied null scan arrives, so a refreshed browser shows the same record or record-not-found view.
- Preserve record-not-found behavior for successfully read IDs that are unknown or unlinked.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mode-state-machine`: Limit the visible NFC error to startup before a successful read, preserve the resolved Standby view after later hardware errors, and ignore externally supplied null scans during Playing.
- `ui-app`: Show the NFC error placeholder only before a successful scan; retain a valid record display through subsequent read failures.
- `api-server`: Seed reconnecting clients with the last successful scan rather than a later externally supplied null scan event.

## Impact

- NFC standby polling in `api/nfc_coordinator.py`.
- Runtime WebSocket event state in `api/main.py` and scan handling in `ui/app.js`.
- Focused NFC coordinator, API state, and UI behavior checks. The scan event shape remains unchanged.
