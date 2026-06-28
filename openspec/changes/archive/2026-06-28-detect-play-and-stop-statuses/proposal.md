## Why

The backend currently does not derive real playback start and stop statuses from platter RPM, so the frontend can only enter Play or Standby from injected events. Runtime detection is needed so hardware playback state is published automatically using the existing frontend event contract.

## What Changes

- Add backend RPM polling every second.
- Detect playback start only after RPM reaches `SPINNING_RPM_THRESHOLD = 4500` and remains in the post-threshold tonearm delay window until `TONEARM_DELAY_AUTO = 10713` milliseconds has elapsed.
- Detect playback stop when RPM falls below `SPINNING_RPM_THRESHOLD = 4500`.
- Broadcast detected play and stop status events to connected frontend clients using the same event format already consumed by the UI.
- Avoid repeatedly sending the same play or stop status while the detected playback state is unchanged.

## Capabilities

### New Capabilities

- `playback-status-detection`: Backend runtime detection of record play and stop statuses from RPM sampling and calibrated tonearm delay timing.

### Modified Capabilities

- `api-server`: Backend WebSocket broadcasting gains an internal RPM-based status event producer that emits the existing frontend status event format.

## Impact

- Affected backend code: API server startup/runtime workers, WebSocket event broadcasting, RPM sensor integration, and tests around backend event producers.
- Affected frontend contract: no format change; frontend continues receiving existing `{"event":"status","data":{"status":"play"}}` and `{"event":"status","data":{"status":"stop"}}` messages.
- Dependencies/systems: hardware RPM source must be sampled safely once per second without blocking Flask/WebSocket handling.
