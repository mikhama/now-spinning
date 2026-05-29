## 1. Play fallback UI

- [x] 1.1 Add a play-mode empty-state layout in `ui/index.html` that reuses the existing record-not-found placeholder pattern.
- [x] 1.2 Update play-mode action-bar selection so no buttons are shown when play is active without a valid current record.

## 2. State and rendering behavior

- [x] 2.1 Update `ui/app.js` play rendering to switch between the normal now-playing layout and the record-not-found fallback based on whether `getCurrentRecord()` resolves.
- [x] 2.2 Ensure `status: "play"` preserves a null `currentRecordId` and does not synthesize a default record after a not-found scan.
- [x] 2.3 Ensure `status: "stop"` returns to standby without losing the existing not-found fallback context.

## 3. Verification

- [x] 3.1 Verify the boardless event flow `scan(record missing) -> status(play) -> status(stop)` shows record-not-found in both play and standby, with no play buttons during the fallback.
- [x] 3.2 Verify valid-record playback and the `#play` debug hash still show the normal play layout and controls.