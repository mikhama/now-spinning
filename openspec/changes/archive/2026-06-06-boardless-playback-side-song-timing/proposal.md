## Why

Boardless Play mode currently treats side and track selection as simple UI indices, so the displayed side label and current song can drift from the elapsed playback time. During real listening, users also sometimes manually advance the side or song to match what they physically selected on the turntable, and those corrections need to become part of the playback timeline.

## What Changes

- Update boardless Play mode so the Side button label always reflects the currently selected side.
- Add elapsed-time-aware side and song selection: playback starts on side A, derives the current song from elapsed time, and treats `status: "play"` with `time` as a spinning turntable.
- Preserve a manually selected side when playback starts for the same record; reset to side A only when a new record is activated.
- Advance to the next side when playback stops at or after 20 seconds before the selected side end, including any overrun beyond the estimated side length.
- Preserve manual side selection during playback by cycling the selected side when the Side button is clicked, including wraparound back to side A.
- Clamp elapsed playback overruns to the last song on the currently selected side instead of crossing to another side while the turntable is spinning.
- Treat manual side and song navigation as timeline corrections: changing side or track after playback has already been running SHALL add the appropriate offset to the effective playback position.
- Clear song correction when playback stops, so restarting the same selected side starts from that side's first song.
- Support both mock and synced record data shapes for side labels and track durations.
- Keep the scope limited to boardless mode for this change.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `ui-app`: Play mode side labels, side button behavior, and prev/next song controls must reflect elapsed-time-aware boardless playback state.
- `mode-state-machine`: Boardless Play runtime state must track effective playback position, side/song offsets, and manual corrections.
- `boardless-events`: Boardless status events must provide elapsed playback time; spinning is derived from `status: "play"` with `time`, while any other status is not spinning.

## Impact

- Affected frontend state, event handling, and Play-mode rendering in `ui/app.js`.
- Affected boardless event examples and usage documentation, including play elapsed time and derived spinning/stopped state.
- No real board, NFC hardware, database schema, or non-boardless event producer changes are proposed.
