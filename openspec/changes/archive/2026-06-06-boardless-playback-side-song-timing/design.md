## Context

Boardless Play mode is driven by WebSocket `status` events and local UI state in `ui/app.js`. The UI already has the record sides and track durations in memory, but it currently treats the selected side and track as direct button indices. The elapsed `time` value is displayed in the top bar but is not used to derive the current side, current track, or manual playback corrections.

The target behavior is boardless-only. Real hardware event production remains out of scope. Boardless status events carry elapsed playback time on `status: "play"`; that combination means the turntable is spinning. Any other status means the turntable is not spinning.

## Goals / Non-Goals

**Goals:**

- Keep the Play-mode Side button label aligned with the selected side at all times.
- Start playback on the first side only after a new record is activated, and otherwise keep side/song display derived from elapsed playback time and manual corrections.
- Preserve a manually selected side when the same record enters Play mode.
- Advance to the next side when playback stops at or after 20 seconds before the selected side end, including any overrun beyond the estimated side length.
- Clamp elapsed playback overruns to the selected side's final song while the turntable is spinning.
- Let the user manually cycle sides during Play mode, including wraparound, and treat that selection as a correction to the effective playback position.
- Let the user use prev/next song controls during Play mode and treat song changes as corrections to the effective playback position.
- Clear song correction when playback stops, so the next Play start begins from the selected side's first song.
- Compute side and track offsets from existing side/track duration data, supporting both `id`/`duration` mock records and `side_label`/`time` synced records.

**Non-Goals:**

- No real board, motor sensor, NFC, or turntable hardware integration changes.
- No database schema changes.
- No new UI screens or controls.
- No attempt to infer exact needle position beyond side/track duration offsets and boardless event elapsed time.

## Decisions

### Keep elapsed timeline state in the frontend

The frontend SHALL keep boardless playback timing state beside the existing Play-mode indices: latest server elapsed seconds, selected side index, selected track index, and a manual offset in seconds. This keeps boardless playback simulation local to the existing UI event path and avoids changing the API data model.

Alternative considered: have the boardless event sender provide side and track directly. That would make tests simpler but would not cover the user correction behavior where side/song buttons intentionally adjust the effective playback position.

### Compute effective playback position from elapsed time plus manual offset

The UI SHALL parse playback time and track durations into seconds and compute `effectivePlaybackSeconds = eventElapsedSeconds + manualOffsetSeconds`. Boardless status playback time uses `MM:SS`; synced record track durations may use either `MM:SS` or `M:SS`. Manual song changes set the effective position to the start of the selected track. Manual side changes preserve the selected song index on the new side when the previous side has not overrun, and clamp to the new side's last song when the previous side has already overrun. The stored manual offset is then recalculated against the latest server elapsed seconds.

Alternative considered: mutate only `currentSideIndex` and `currentTrackIndex`. That preserves the current UI behavior but leaves later automatic updates unaware of the user's correction.

### Derive side and track from durations through shared helpers

Implement helpers for parsing duration strings, summing track durations, getting side start/end offsets, finding the side for an effective elapsed time, and finding the track inside a side. Side labels SHALL support `side.id` and synced `side.side_label`; track durations SHALL support `track.duration` and synced `track.time`. Render and navigation should consume these helpers rather than duplicating duration math.

Alternative considered: compute side duration in each button handler. That would be quicker but makes edge cases around wraparound and offset preservation harder to test.

### Derive spinning from status

The UI SHALL NOT store a separate `spinning` payload field. A boardless `status: "play"` event with valid `MM:SS` `time` means the turntable is spinning. Any other status means the turntable is not spinning and Play-only timing state is cleared.

Alternative considered: accept a boolean `spinning` field on play events. That duplicates information already represented by the status contract and creates unnecessary backend/runtime state.

### Preserve same-record manual side selection on Play start

When a new record is activated, the UI SHALL reset selected side and track to the first side/track. When the same record later receives `status: "play"` after the user manually selected a side, the UI SHALL translate the selected side/track into the manual playback offset before resolving elapsed playback, so Play starts from that selected side instead of snapping back to side A.

### Keep elapsed playback on the selected side while spinning

While `status: "play"` with valid time indicates the turntable is spinning, elapsed playback SHALL resolve the current track only within the currently selected side. If effective playback exceeds the selected side's estimated duration, the UI SHALL show that side's last song rather than moving to another side. Side advancement is reserved for manual Side clicks and stopped-turntable side-end handling.

## Risks / Trade-offs

- [Risk] Track durations may be missing or malformed. -> Mitigation: treat invalid durations as `0` and keep existing index fallback behavior instead of crashing.
- [Risk] Side selection could fight a user's deliberate manual side repeat. -> Mitigation: manual side changes recalculate the playback offset, so the next effective position reflects the user's chosen side.
- [Risk] Event payload naming for stopped/spinning could drift. -> Mitigation: derive spinning from `status: "play"` with `time` instead of accepting another payload field.
- [Risk] Duration math can introduce subtle off-by-one behavior near boundaries. -> Mitigation: add focused unit-style or browser tests around side end tolerance, overrun clamping, wraparound, and manual offset recalculation.
