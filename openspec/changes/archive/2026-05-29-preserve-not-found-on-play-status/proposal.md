## Why

When the UI is in the standby record-not-found state and a `status: "play"` event arrives, it currently renders stale record metadata and controls instead of preserving the empty-state placeholder. That breaks the runtime contract that record details only appear after a valid record has been established, and it makes a missing record look like a real album is playing.

## What Changes

- Tighten mode-transition behavior so a play status without an active valid record keeps the record-not-found fallback instead of exposing record artwork, metadata, or playback controls.
- Define the play-mode empty-state rendering contract for cases where no current record is available.
- Keep valid play behavior unchanged when a scanned record exists and playback starts normally.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mode-state-machine`: Clarify how `status` play events behave when no valid current record is active after a not-found scan.
- `ui-app`: Clarify that play mode must not render cover art, artist/album text, track details, or action buttons when playback is entered without a valid current record.

## Impact

- Affected frontend state/rendering in `ui/app.js`.
- Affected mode and view requirements in the OpenSpec contracts for `mode-state-machine` and `ui-app`.
- No API or dependency changes.