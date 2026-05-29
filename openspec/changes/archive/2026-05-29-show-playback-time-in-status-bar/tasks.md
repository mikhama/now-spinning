## 1. Frontend playback-time state and rendering

- [x] 1.1 Add a dedicated playback-time field to the UI runtime state in `ui/app.js`, populate it from boardless `status: "play"` events, and clear it on `status: "stop"` without regressing the current record / standby-error preservation behavior.
- [x] 1.2 Update the top-bar mode-label rendering path so Play mode shows `PLAY {mm:ss}` when a valid playback time is available and plain `PLAY` otherwise.

## 2. Boardless event usage and docs

- [x] 2.1 Update boardless-mode status-event examples and any related developer-facing docs to use `{"event":"status","data":{"status":"play","time":"00:01"}}` for Play-mode testing.
- [x] 2.2 Update `README.md` usage so the documented boardless play event includes the new `time` payload and keeps the scope limited to boardless-mode testing.

## 3. Verification

- [x] 3.1 Verify that posting a boardless `status` play event with `time: "00:01"` renders `PLAY 00:01` in the UI top bar.
- [x] 3.2 Verify that a subsequent `status` stop event returns the UI to Standby, removes the playback time from the top bar, and preserves the existing record or not-found fallback context.
- [x] 3.3 Verify that hash-based dev mode still ignores live status events, so the new playback-time path is exercised through boardless event injection rather than URL hashes.