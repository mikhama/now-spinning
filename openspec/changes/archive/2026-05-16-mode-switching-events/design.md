## Context

The Now Spinning UI has six modes (standby, play, link, re-link, stylus, sync) controlled by a `nextMode()` function that cycles through a flat `MODES` array. Mode transitions also happen via WebSocket events (`status: playing/idle`) and URL hash routing for development. The backend (`api/main.py`) has a WebSocket endpoint that sends initial state on connection but doesn't accept incoming messages. Boardless mode (`BOARDLESS_MODE=true`) currently only applies to NFC read/write simulation in `lib/nfc.py`.

## Goals / Non-Goals

**Goals:**
- Implement a mode button that cycles through a specific subset of modes in a defined order
- Implement event-driven mode transitions for scan, play/stop, and link-error events
- Provide a minimal boardless event publishing mechanism via a simple HTTP endpoint that injects events into the WebSocket broadcast
- Keep the switch between boardless and hardware modes trivial (same WebSocket protocol, just different event source)

**Non-Goals:**
- Real NFC scanning integration (hardware events will come later)
- Actual turntable spin detection
- Sync process implementation
- UI visual changes beyond mode switching behavior

## Decisions

1. **Mode button cycles a specific subset, not all modes.** The mode button cycles: standby → sync → link → re-link → stylus → standby. Play mode is never reached via button — only via events. Error states (standby-error, standby-not-found, link-error, stylus-error) are sub-states within their parent mode, not separate entries in the cycle. When in standby-not-found, the button press goes to sync (same as standby). When styli list is empty, stylus mode shows the error state automatically.

2. **Events use the existing WebSocket protocol.** Events are JSON messages with `{event, data}` structure, matching the existing pattern. New event types:
   - `scan` with `{record_id: "<id>" | null}` — null means NFC error, unknown id means not-found
   - `status` with `{status: "play"}` — turntable started spinning
   - `status` with `{status: "stop"}` — turntable stopped
   - `link_error` with `{record_id: "<id>"}` — linking process failed

3. **Boardless event publishing via POST endpoint.** Add `POST /events` endpoint that accepts the same `{event, data}` JSON and broadcasts it to all connected WebSocket clients. This is the simplest approach — events can be sent with `curl -X POST -d '{"event":"scan","data":{"record_id":"1"}}' localhost:5000/events`. No separate script needed, just curl from another terminal.

4. **WebSocket becomes bidirectional.** The WebSocket handler loop (`while True: ws.receive()`) is updated to parse received messages and broadcast them. This means in hardware mode, the backend process can also send events to the UI by writing to the WebSocket, and in boardless mode, the POST endpoint injects events through the same broadcast mechanism.

5. **Connected clients list.** Maintain a simple set of connected WebSocket clients in the Flask app so the POST endpoint can broadcast to all of them. This is a minimal in-process list, not a message queue.

## Risks / Trade-offs

- **Single-process broadcasting** — The connected clients set only works within a single Flask process. This is fine for the Raspberry Pi deployment (single process, single client). If multi-process is ever needed, a proper message bus would be required.
- **No authentication on POST /events** — The endpoint is open. Acceptable for a local-network Raspberry Pi device, not suitable for public deployment.
- **Mode button order is hardcoded** — The cycle order is a fixed array. Changing it requires a code change. This is acceptable for a dedicated appliance UI.
