## 1. Playback Timing Helpers

- [x] 1.1 Add frontend helpers in `ui/app.js` to parse `MM:SS`/`M:SS` durations into seconds and safely handle missing or malformed durations.
- [x] 1.2 Add helpers to calculate side start offsets, side durations, track start offsets, and total record duration from existing record side/track data, including synced `side_label`/`time` fields.
- [x] 1.3 Add helpers to resolve an effective playback position to `{sideIndex, trackIndex}` and to clamp or wrap side/song indices across record boundaries.

## 2. Boardless Playback State

- [x] 2.1 Extend Play-mode runtime state with latest boardless elapsed seconds and manual playback correction offset.
- [x] 2.2 Reset boardless playback timing state when a new valid record scan is activated, when active record state is cleared, and when playback stops; clear selected song to the first song on stop.
- [x] 2.3 Update `status: "play"` event handling to parse `time`, derive spinning from play-with-time status, refresh effective side/song selection, and keep hash dev mode ignoring live status events.

## 3. Play Side And Song Controls

- [x] 3.1 Update Play-mode side selection so playback starts on the first side only for a newly activated record and the Side button label always reflects the selected side.
- [x] 3.2 Update side-end handling to keep the selected side while `status: "play"` with `time` indicates the turntable is spinning, clamp overruns to the selected side's last song, then advance to the next side on stop at/after the 20-second side-end tolerance including overruns.
- [x] 3.3 Update Side button handling during Play mode to cycle sides and recalculate the manual playback correction offset from the selected side, preserving selected song index before overrun and clamping to the selected side's last song after overrun.
- [x] 3.4 Update Prev/Next song handling during Play mode to select the adjacent song and recalculate the manual playback correction offset from the selected song.
- [x] 3.5 Preserve existing Standby side button behavior while applying the elapsed-time-aware behavior only to Play mode.

## 4. Boardless Usage And Docs

- [x] 4.1 Update boardless event examples or README usage so Play-mode testing includes `time` and documents derived spinning/stopped status.
- [x] 4.2 Keep the documented scope clear that this timing behavior is boardless-only and does not change real board event production.

## 5. Verification

- [x] 5.1 Verify a boardless `status: "play"` event starts Play mode on side A and shows the matching first track and Side button label.
- [x] 5.2 Verify elapsed playback selects the expected track from track durations on the active side and clamps elapsed overruns to that side's last song.
- [x] 5.3 Verify side-end handling keeps the selected side while `status: "play"` with `time` indicates spinning and advances on stop within tolerance or after overrun.
- [x] 5.4 Verify no separate `spinning` payload state is stored.
- [x] 5.5 Verify manual Side, Prev song, and Next song clicks during playback update the displayed side/song and affect later elapsed-time updates through the correction offset, and verify stop/start clears song correction.
