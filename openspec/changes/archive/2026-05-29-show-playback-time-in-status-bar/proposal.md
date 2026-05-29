## Why

Play mode currently shows only the mode label in the top status bar, so there is no visible playback clock even when the server already knows the current elapsed time. Adding a server-driven `MM:SS` clock beside `PLAY` makes the screen more useful during playback while keeping the change scoped to boardless-mode event input for now.

## What Changes

- Update the Play-mode top status bar contract so the left label renders `PLAY {mm:ss}` when a play status event includes a playback time.
- Update the status event handling contract so boardless-mode `status: "play"` events may carry a `time` field and the UI uses that value during Play mode.
- Update boardless development usage so the README and boardless event examples send `{"event":"status","data":{"status":"play","time":"00:01"}}` instead of a play status without elapsed time.
- Keep the scope limited to boardless mode and UI rendering; this change does not propose new real hardware board event emission.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `ui-app`: Play mode status-bar rendering and live status-event handling must support a server-provided playback time in `MM:SS` format.
- `mode-state-machine`: Play status events must preserve the provided playback time in runtime state so Play mode can render it and Stop can clear the Play-only display.
- `boardless-events`: Boardless-mode play event examples and contract must include the optional playback `time` payload used to test the UI.

## Impact

- Affected frontend state/rendering in `ui/app.js` and the top-bar display defined by the UI app spec.
- Affected boardless event documentation and developer usage in `README.md`.
- No real board integration, NFC hardware flow, or non-boardless event producer changes are proposed.