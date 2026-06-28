## Context

The Flask backend already broadcasts frontend events through `broadcast_message`, stores the latest runtime status in `runtime_state`, and starts a daemon temperature publisher from `api/main.py`. Boardless/manual events use the same message shape the UI already consumes: `{"event": "status", "data": {"status": "play"}}` and `{"event": "status", "data": {"status": "stop"}}`.

RPM measurement currently exists only in experimental scripts under `exp/`, including the calibrated constants `SPINNING_RPM_THRESHOLD = 5500` and a one-second sample interval. The runtime backend needs a hardware-aware event producer that reuses the established broadcast path without changing the frontend contract.

## Goals / Non-Goals

**Goals:**

- Poll platter RPM once per second from the backend runtime.
- Emit a single `status: "play"` event only after RPM reaches `5500` and `9726` milliseconds have elapsed from that threshold crossing.
- Emit a single `status: "stop"` event when RPM falls below `5500` after playback was considered active.
- Keep the existing WebSocket/event payload format unchanged.
- Make the detection state machine unit-testable without GPIO hardware.

**Non-Goals:**

- Add frontend event handling or UI changes.
- Add elapsed playback `time` values to hardware-derived play events.
- Recalibrate the RPM threshold or tonearm delay values.
- Replace boardless `/events` status injection.

## Decisions

### Use a dedicated playback status detector

Implement the threshold/delay logic in a small backend unit separate from Flask routing, for example `api/playback_status.py`. It should accept injected `read_rpm`, `broadcast`, and clock/sleep functions so tests can drive exact RPM and timing sequences without Raspberry Pi hardware.

Alternative considered: put the logic directly in `api/main.py` beside the temperature publisher. That would be faster initially but would make the state transitions harder to test and would grow an already broad module.

### Model detection as a state machine

Track three runtime states:

- `stopped`: RPM is below threshold and playback is not active.
- `threshold_reached`: RPM has reached `SPINNING_RPM_THRESHOLD`, and the detector is waiting for `TONEARM_DELAY_AUTO` to elapse.
- `playing`: the delay has elapsed and a play event has already been emitted.

When RPM drops below threshold in either `threshold_reached` or `playing`, reset to `stopped`. Only emit `stop` when leaving `playing`; a brief startup that never completes the delay should not generate a stop event.

Alternative considered: derive state only from the latest RPM sample. That cannot represent the required tonearm delay and would risk repeated play events on every poll after the threshold is reached.

### Reuse the existing broadcast path

Detected status changes should call `broadcast_message` with the existing payload shape:

- Play: `{"event": "status", "data": {"status": "play"}}`
- Stop: `{"event": "status", "data": {"status": "stop"}}`

This keeps `runtime_state`, initial WebSocket events, and all connected clients consistent with boardless events.

Alternative considered: add a new event type such as `playback_status`. That would require frontend changes and duplicate semantics already covered by `status`.

### Start the publisher once, like temperature publishing

Add `playback_status_publisher_started` and a lock mirroring the temperature publisher pattern. The entry point should start the playback publisher alongside `start_temperature_publisher()`. Tests should be able to verify the publisher starts once and does not spawn duplicate polling threads.

Alternative considered: start polling lazily when the first WebSocket client connects. That saves work when no UI is connected, but it can miss the start of playback and makes initial runtime state less reliable.

### Keep hardware access behind an RPM reader

Use an RPM reader abstraction so the detector can run with a real GPIO-backed reader on the target device and with a no-op/`None` reader in environments without GPIO support. If hardware read setup fails, the publisher should log the issue and not crash the Flask server.

Alternative considered: import and initialize `gpiozero` unconditionally. That would make local development and tests fail on non-Raspberry Pi machines.

## Risks / Trade-offs

- [Risk] A one-second polling interval can detect the exact stop moment up to one second late. → Mitigation: this matches the requested sampling cadence and keeps backend load low.
- [Risk] RPM may briefly dip below threshold during playback and cause a stop event. → Mitigation: implement exactly the requested below-threshold rule now; add debounce later only if hardware measurements show false stops.
- [Risk] Startup threshold crossing may be followed by a drop before the tonearm delay elapses. → Mitigation: reset the pending timer when RPM falls below threshold and do not emit play.
- [Risk] GPIO dependencies may be unavailable outside target hardware. → Mitigation: lazy hardware imports and dependency injection keep tests/development functional.

## Migration Plan

1. Add unit tests for detector state transitions using injected RPM values and monotonic time.
2. Add the playback publisher and start-once guard.
3. Wire the publisher into `api/main.py` startup beside the existing temperature publisher.
4. Verify existing `/events` boardless status behavior remains unchanged.

Rollback is straightforward: stop calling the playback publisher startup function from the server entry point. Boardless/manual status event behavior remains available.

## Open Questions

- Which concrete hardware RPM reader should runtime use first: a promoted version of the `exp/` pulse-counting implementation, or an existing device API if one is added elsewhere?
- Should hardware-derived `play` events eventually include elapsed `time`, or should elapsed time remain frontend-derived for this path?
