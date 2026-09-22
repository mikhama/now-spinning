## Why

A transient NFC read failure can leave the standby UI stuck on “NFC Reading Error” even after the same linked record is read successfully again. The coordinator suppresses the recovery scan as a duplicate because it remembers the record ID that was emitted before the error.

## What Changes

- Treat an emitted NFC read error as a distinct observable scan state.
- Emit the next successful standby scan after an error, including when it resolves to the same record ID that was active before the error.
- Preserve duplicate suppression for uninterrupted successful reads of the same record and preserve no-card behavior.
- Add regression coverage for same-record recovery after a transient read failure.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `mode-state-machine`: Require standby NFC polling to notify the frontend when the same record successfully recovers from an emitted NFC read error.

## Impact

- `api/nfc_coordinator.py`: standby scan event-state tracking and recovery emission.
- `tests/test_nfc_coordinator.py`: coordinator regression coverage.
- Existing WebSocket event shapes and frontend behavior remain unchanged.
