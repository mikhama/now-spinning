## Context

The current UI top bar renders its left label from the active mode name only, and the WebSocket `status` handler in `ui/app.js` only flips between `play` and `standby`. There is no runtime field for server-provided playback time, and the boardless-mode README examples still publish `status: "play"` without a `time` value.

This change is intentionally small but crosses three contracts: the UI top-bar display, the mode-state event handling that stores play-state inputs, and the boardless-mode event examples used during development. The requested scope excludes real hardware board event emission, so the only event contract change in this proposal is the boardless `/events` workflow and its documentation.

## Goals / Non-Goals

**Goals:**
- Display `PLAY {mm:ss}` in the top status bar when Play mode has a server-provided playback time.
- Store playback time from boardless `status` play events in UI runtime state so the top bar can re-render consistently.
- Keep the server as the source of truth for elapsed time instead of introducing a client-side timer.
- Update boardless usage documentation so local testing uses the new payload shape.

**Non-Goals:**
- Implement real board or sensor-driven event emission.
- Add a continuously ticking client clock when no server update arrives.
- Redesign the top bar layout or add a separate playback-time field elsewhere in the UI.
- Change Standby, Link, Re-Link, Stylus, or Sync labels beyond existing behavior.

## Decisions

### Store playback time as explicit UI state
Add a dedicated playback-time field to the frontend runtime state and update it from `status` events. This keeps top-bar rendering declarative and avoids coupling display logic to the last raw WebSocket message.

Alternative considered: derive the display directly inside the WebSocket handler and write it to the DOM immediately. Rejected because it bypasses the existing render/input-diff flow and makes later re-renders harder to reason about.

### Treat the server value as the display-ready source of truth
The client should render the provided `time` string as the playback clock when it is present in `MM:SS` form, rather than starting a local interval or recomputing elapsed time. This keeps boardless mode and eventual production event sources aligned around a single authoritative time payload.

Alternative considered: start a client-side timer from the received value and let the UI keep counting locally. Rejected because drift, reconnects, and paused playback states would make the display diverge from server state.

### Format the top-bar label through the existing mode-label path
The top bar already reads a single mode-label value from the render pipeline. Extending that path to produce `PLAY 00:01` in Play mode keeps the layout unchanged and limits the implementation to state plus a small display helper.

Alternative considered: add a second DOM node for playback time inside the top bar. Rejected because it expands the layout surface for a single string that naturally belongs with the mode label.

### Keep the event-contract change boardless-only in this proposal
The proposal should update the boardless `/events` payload examples, related docs, and the UI path that consumes them, but it should not introduce any new real board event emission work.

Alternative considered: broaden the change to all status-event producers immediately. Rejected because the user explicitly asked to keep this proposal limited to boardless mode.

## Risks / Trade-offs

- [Risk] A stale playback time could remain visible after leaving Play mode. -> Mitigation: clear the stored playback time on `status: "stop"` and whenever record/error reset paths intentionally leave Play mode.
- [Risk] A malformed `time` value could render an inconsistent label. -> Mitigation: treat only zero-padded `MM:SS` strings as displayable and fall back to the plain `PLAY` label when the payload is missing or invalid.
- [Risk] Hash-based dev mode will continue ignoring live status events, so `#play` alone will not exercise the server-driven clock. -> Mitigation: keep the existing hash behavior unchanged and document the boardless `curl` example as the intended way to test the clock.