## Why

The NFC coordinator currently turns a successfully read but unlinked record ID into the same `record_id: null` payload used for NFC read failures. The frontend therefore shows “NFC Reading Error” even though the reader worked and the correct user-facing result is “Record Not Found.”

## What Changes

- Preserve the distinction between a genuine NFC read failure and a successfully read tag whose record is not linked.
- Route unlinked and unknown scanned record IDs to the existing standby “Record Not Found” state without activating record metadata.
- Keep `record_id: null` reserved for NFC read failures so the existing “NFC Reading Error” state remains accurate.
- Add regression coverage for coordinator scan payloads and frontend handling of unlinked scans.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mode-state-machine`: Define unlinked standby scan behavior separately from NFC read errors and require a not-found result for unlinked record IDs.
- `ui-app`: Extend the standby “Record Not Found” behavior to records present in the collection but not linked for playback.

## Impact

- Affected code: `api/nfc_coordinator.py`, `ui/app.js`, and their focused tests.
- Event compatibility: successful reads continue to use `scan` events with the scanned `record_id`; `record_id: null` remains the NFC read-error signal.
- No database schema, hardware protocol, dependency, or public HTTP endpoint changes.
