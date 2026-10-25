## Why

Termination during a Standby read can stop the process before RF cleanup. This gap is confirmed by a subprocess check. The cause of the reported I2C restart failure is not confirmed.

## What Changes

- Close an existing NFC backend once. Do not initialize a reader during cleanup.
- Stop new NFC work, discard queued work, let the active operation finish, and close the reader in the worker.
- Use one cleanup path for signals, server exit, and process exit. Wait up to five seconds for the worker and reader cleanup.
- Return JSON 503 for NFC mode and write requests during shutdown. Keep the existing Exit response and stylus persistence checks.
- Log mode changes, operation results, transport errors, and cleanup results. Report the actual I2C diagnostic error.
- Add local regression tests and a separate Pi verification record for both reported sequences.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `nfc-library`: Add safe backend close and preserve transport failure details.
- `api-server`: Add worker shutdown, bounded exit cleanup, request rejection, and diagnostic logs.

## Impact

Changes affect `lib/nfc.py`, `api/nfc_coordinator.py`, `api/main.py`, the I2C diagnostic, and tests. NFC timing, tag formats, and hardware configuration stay the same. Hardware reset and bus recovery require more evidence and are outside this change. Keep this change open. Do not sync or archive it. Do not change README edits or the separate stylus-hours change.
