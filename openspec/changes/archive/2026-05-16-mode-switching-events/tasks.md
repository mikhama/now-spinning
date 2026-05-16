## 1. Backend — WebSocket client tracking and event broadcast

- [x] 1.1 Add a global `connected_clients` set to `api/main.py` and update the `/ws` handler to add/remove clients on connect/disconnect
- [x] 1.2 Add `POST /events` endpoint that accepts `{event, data}` JSON and broadcasts to all connected WebSocket clients
- [x] 1.3 Update the WebSocket receive loop to handle incoming messages (parse JSON, broadcast to other clients)

## 2. Frontend — Mode button cycle

- [x] 2.1 Replace `nextMode()` in `ui/app.js` with a new cycle order: standby → sync → link → re-link → stylus → standby (play is skipped; error sub-states map to their parent mode)
- [x] 2.2 When in play mode and mode button is pressed, transition to standby

## 3. Frontend — Event-driven mode transitions

- [x] 3.1 Add `scan` event handler in WebSocket `onmessage`: set `currentRecordId`, clear/set `standbyError` based on record_id (null → "nfc", unknown → "not-found", valid → clear), transition to standby mode
- [x] 3.2 Update `status` event handler: `"play"` → play mode, `"stop"` → standby mode (replace existing `"playing"`/`"idle"` checks)
- [x] 3.3 Add `link_error` event handler: set `linkError = true` and re-render

## 4. Verification

- [x] 4.1 Start the server with `BOARDLESS_MODE=true`, open UI, and test mode button cycling through standby → sync → link → re-link → stylus → standby
- [x] 4.2 Use curl to send `scan`, `status` (play/stop), and `link_error` events via `POST /events` and verify UI transitions
