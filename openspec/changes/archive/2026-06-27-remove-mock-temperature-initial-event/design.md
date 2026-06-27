## Context

The backend currently stores `runtime_state["temperature_c"] = 59`, so newly connected WebSocket clients can receive a fabricated board temperature before any hardware read occurs. The frontend also calls `/temperature` on load and every 30 seconds, which means temperature refresh is client-driven rather than owned by the backend event stream.

The UI already understands `temperature_c` WebSocket events and renders `null` as `N/A`, so the main behavior change is on event production and initialization.

## Goals / Non-Goals

**Goals:**
- Ensure initial temperature state is unavailable (`temp_c: null`) until a real backend read succeeds.
- Broadcast backend-owned `temperature_c` events every 30 seconds.
- Represent unavailable reads as `null`, never as a mock fallback value.
- Remove the `/temperature` endpoint and make WebSocket events the only frontend temperature source.

**Non-Goals:**
- Change the top-bar temperature formatting.
- Add configuration for the polling interval.
- Add historical temperature storage.

## Decisions

1. Initialize runtime temperature as `None` and include a nullable initial temperature event.

   New clients need a deterministic temperature event so the top bar can settle immediately to `N/A`. Using `null` preserves the existing frontend state contract and avoids introducing a string sentinel like `"N/A"` into event payloads.

   Alternative considered: omit the initial temperature event until the first successful read. Rejected because the requested behavior is to send `N/A` initially, and explicit `null` is easier to test.

2. Make the backend own the 30-second refresh loop.

   A background worker in `api/main.py` will read the current temperature and call the existing WebSocket broadcast path with `{"event": "temperature_c", "data": {"temp_c": value_or_null}}`. This keeps all connected clients in sync without each browser tab polling independently.

   Alternative considered: keep frontend polling and post the result back to runtime state. Rejected because the browser should not be responsible for hardware monitoring.

3. Replace the REST temperature route with a backend-only read helper.

   The implementation should factor the sysfs read into a helper used by the periodic publisher. Read failures return `None` and log server-side; no mock value is substituted. The helper stays internal to the backend because the UI only needs the WebSocket event stream.

   Alternative considered: keep `/temperature` as a fallback or diagnostic endpoint. Rejected because the requested product path is server-owned event delivery, and leaving a parallel endpoint invites frontend polling to return.

4. Start the publisher when the Flask app runs.

   The periodic worker should start with the API process and run as a daemon thread. It should emit every 30 seconds after startup; the initial WebSocket connection event remains `null`, so clients do not need to wait for the first read to display `N/A`.

   Alternative considered: start one publisher per WebSocket connection. Rejected because multiple clients would create duplicated hardware reads and duplicated broadcasts.

## Risks / Trade-offs

- [Risk] Flask debug reloader could start duplicate background threads. -> Mitigation: guard worker startup so it only starts once per process.
- [Risk] Broadcasting from a background thread can encounter stale WebSocket clients. -> Mitigation: reuse `broadcast_message`, which already removes clients that fail on send.
- [Risk] Tests may become timing-sensitive if they wait for real 30-second intervals. -> Mitigation: test the read/publish helper directly and avoid sleeping in unit tests.
