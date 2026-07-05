## Why

The app can currently start serving requests even when required hardware sensors are unavailable, because sensor initialization failures can be handled inside background workers after startup. This hides deployment wiring problems and leaves the process running in a degraded state when the expected hardware-backed mode cannot operate.

## What Changes

- Add an explicit startup readiness check for the required hardware sensors before the API server starts its long-running workers.
- Validate both the NFC sensor path and RPM playback sensor path at the beginning of startup when boardless mode is disabled.
- Fail immediately with a clear startup error when either required sensor cannot be initialized or cannot complete its readiness probe.
- Preserve boardless mode behavior so hardware sensor readiness is not required when `BOARDLESS_MODE=true`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `api-server`: Startup behavior changes from tolerating unavailable hardware to failing immediately when required sensors are not ready in hardware mode.
- `playback-status-detection`: RPM sensor setup changes from background-worker-only initialization to an explicit startup readiness requirement.

## Impact

- Affected code: `api/main.py`, `api/playback_status.py`, `api/nfc_coordinator.py` or NFC initialization helpers, and related tests.
- Runtime behavior: hardware-mode startup will exit/fail if either required sensor is unavailable; boardless mode remains usable without physical sensors.
- APIs: no HTTP or WebSocket response shapes change.
- Dependencies: no new external dependencies expected.
