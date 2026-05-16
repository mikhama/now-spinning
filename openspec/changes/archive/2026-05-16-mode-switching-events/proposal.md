## Why

The UI currently uses a flat `nextMode()` cycle and URL-hash routing for mode switching, with no structured event system. Real-world operation requires modes to transition based on hardware events (NFC scan, turntable spin) and user actions (mode button). We need a proper state machine for mode transitions and a simple way to publish events from the terminal in boardless mode for development without hardware.

## What Changes

- Replace the flat `nextMode()` cycle with a structured mode button cycle that follows a specific order: standby/standby-not-found → sync → link → re-link → stylus/stylus-error
- Add event-driven mode transitions:
  - `scan` event (with record_id or null) → transitions to standby or standby-error/standby-not-found
  - `status: play` event → transitions to play mode
  - `status: stop` event → transitions back to standby mode
  - `link-error` event → transitions to link-error state when linking fails
- Add a boardless event publishing mechanism via WebSocket so events can be sent from the terminal using a simple CLI command (e.g., curl or a tiny Python script)
- Backend WebSocket handler accepts incoming event messages in boardless mode and broadcasts them to connected UI clients

## Capabilities

### New Capabilities
- `mode-state-machine`: Defines the mode button cycle order and event-driven transition rules between UI modes
- `boardless-events`: Simple terminal-based event publishing for boardless development mode, allowing events to be sent to the UI via WebSocket

### Modified Capabilities
- `ui-app`: Mode button cycle changes from flat MODES array rotation to a specific ordered sequence; WebSocket handler processes new event types for mode transitions
- `api-server`: WebSocket endpoint enhanced to accept and broadcast events in addition to sending initial state

## Impact

- `ui/app.js` — `nextMode()` rewritten with new cycle order; WebSocket `onmessage` handler extended with scan/link-error events
- `api/main.py` — WebSocket handler updated to receive and broadcast messages; boardless event injection support
- New utility script or endpoint for publishing events from terminal in boardless mode
