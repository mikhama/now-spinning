## MODIFIED Requirements

### Requirement: Play mode — now playing display
In Play mode, the UI SHALL display the current record's cover image, catalogue number, artist, title, a currently playing track label (blue accent), current side label, and prev/next song navigation only when a valid current record with playable side data is loaded. When the current track provides a non-empty artist that is separate from the album-level record artist, the track label SHALL render as `{song_title} ({artist})`. Otherwise, the track label SHALL render as the track title only. The Side button label SHALL always render the currently selected side as `Side {side.id}` when `id` is available, or `Side {side.side_label}` when synced record data uses `side_label`.

#### Scenario: Track is playing
- **WHEN** the mode is Play and a record with tracks is loaded
- **THEN** the UI SHALL show the cover image, `#<id>`, artist, title, track label, side label, and `<Prev` / `Next>` buttons

#### Scenario: Track has a separate artist
- **WHEN** the mode is Play and the current track has a non-empty `artist` value that differs from the current record's `artist`
- **THEN** the track label SHALL render as `{track.title} ({track.artist})`

#### Scenario: Track uses album artist
- **WHEN** the mode is Play and the current track has no `artist` value or the track `artist` matches the current record's `artist`
- **THEN** the track label SHALL render as `{track.title}` with no artist suffix

#### Scenario: Side label reflects current side in Play
- **WHEN** the mode is Play and the selected side is side "B"
- **THEN** the Side button SHALL display `Side B`

#### Scenario: Side label uses synced side label
- **WHEN** the mode is Play and the selected synced side provides `side_label: "B"` instead of `id`
- **THEN** the Side button SHALL display `Side B`

#### Scenario: Side switching in Play
- **WHEN** the user clicks the Side button in Play mode while a valid record is loaded
- **THEN** the UI SHALL cycle to the next side
- **AND** the Side button label SHALL update to that side
- **AND** the current track index SHALL be recalculated from the corrected playback position for the selected side

### Requirement: WebSocket event handling
The UI SHALL establish a WebSocket connection to `/ws` and process incoming events to update the display in real time. WebSocket status events SHALL be ignored when a URL hash is present (dev mode). When no URL hash is present, a `status` event with `{"status": "play", "time": "MM:SS"}` SHALL transition the UI to Play mode, update the playback time shown in the top bar, and represent a spinning turntable. The UI SHALL NOT store a separate `spinning` payload field. A `status` event with `{"status": "stop"}` SHALL return the UI to Standby mode, represent a non-spinning turntable, and remove the Play-only playback time display.

#### Scenario: Receive stylus hours event
- **WHEN** the WebSocket sends `{"event": "stylus_hours", "data": {"hours": 90, "stylus_id": "1"}}`
- **THEN** the UI SHALL update the stylus hours display

#### Scenario: Receive scan event
- **WHEN** the WebSocket sends `{"event": "scan", "data": {"record_id": "1"}}`
- **THEN** the UI SHALL update the current record display

#### Scenario: Receive status play event with time
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "play", "time": "00:01"}}` and no URL hash is present
- **THEN** the UI SHALL switch to Play mode
- **AND** the top bar SHALL render `PLAY 00:01`

#### Scenario: Receive status play event derives spinning state
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "play", "time": "03:30"}}` and no URL hash is present
- **THEN** the UI SHALL store the elapsed playback time
- **AND** the UI SHALL treat the turntable as spinning
- **AND** the UI SHALL NOT store a separate `spinning` payload value

#### Scenario: Receive status stop event
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "stop"}}` and no URL hash is present
- **THEN** the UI SHALL switch to Standby mode
- **AND** the top bar SHALL stop rendering a playback time next to the mode label

#### Scenario: Receive status event with hash
- **WHEN** the WebSocket sends a status event and a URL hash is present
- **THEN** the UI SHALL ignore the status event

## ADDED Requirements

### Requirement: Boardless Play elapsed side and song selection
In boardless Play mode, the UI SHALL derive the current track from the effective playback position within the currently selected side. Playback SHALL start on the first side only after a new record is activated. The effective playback position SHALL be the latest boardless elapsed playback time plus any manual side or song correction offset. Track and side durations SHALL be calculated from existing record side track durations, accepting both `duration` and synced `time` fields.

#### Scenario: Playback starts on side A
- **WHEN** boardless Play mode starts after a new record is activated whose first side label is "A"
- **THEN** the selected side SHALL be side "A"
- **AND** the Side button SHALL display `Side A`

#### Scenario: Playback starts on manually selected same-record side
- **WHEN** the current record is unchanged
- **AND** the user manually selected side "B" before boardless Play mode starts
- **THEN** the selected side SHALL remain side "B"
- **AND** the Side button SHALL display `Side B`

#### Scenario: Elapsed time selects track within side
- **WHEN** boardless Play mode has an effective playback position that falls inside the second track on side "A"
- **THEN** the displayed now-playing track SHALL be the second track on side "A"
- **AND** the Side button SHALL display `Side A`

#### Scenario: Elapsed overrun stays on selected side
- **WHEN** boardless Play mode has an effective playback position beyond the estimated duration of selected side "A"
- **THEN** the displayed now-playing track SHALL be the last track on side "A"
- **AND** the Side button SHALL display `Side A`

#### Scenario: Elapsed overrun follows manually selected side
- **WHEN** boardless Play mode has an effective playback position beyond the estimated duration of the record side
- **AND** the user clicks the Side button from side "A" to side "B"
- **THEN** the displayed now-playing track SHALL be the last track on side "B"
- **AND** the Side button SHALL display `Side B`

#### Scenario: Side advancement waits while status play means spinning
- **WHEN** the effective playback position is at or after 20 seconds before the current side end, including overrun beyond the estimated side length
- **AND** the latest boardless status is `status: "play"` with `time`
- **THEN** the UI SHALL keep the currently selected side

#### Scenario: Side advancement happens after stopped turntable
- **WHEN** the effective playback position is at or after 20 seconds before the current side end
- **AND** the latest boardless status is `status: "stop"`
- **THEN** the UI SHALL advance to the next side
- **AND** the Side button SHALL display that next side

#### Scenario: Side advancement includes elapsed overrun after stopped turntable
- **WHEN** the effective playback position is beyond the estimated current side end
- **AND** the latest boardless status is `status: "stop"`
- **THEN** the UI SHALL advance to the next side
- **AND** the selected song SHALL reset to the first song on that side

#### Scenario: Manual side change corrects playback position
- **WHEN** the user clicks the Side button during boardless Play mode after elapsed playback time has already passed
- **THEN** the UI SHALL cycle to the next side
- **AND** the UI SHALL recalculate the manual playback offset so the effective playback position points at the selected side
- **AND** later elapsed-time updates SHALL keep using that corrected effective playback position

#### Scenario: Manual side change preserves selected song index before overrun
- **WHEN** the user has selected the second song on side "A" during boardless Play mode
- **AND** the effective playback position has not overrun side "A"
- **WHEN** the user clicks the Side button
- **THEN** the selected side SHALL become side "B"
- **AND** the selected song SHALL be the second song on side "B" when it exists

#### Scenario: Manual song navigation corrects playback position
- **WHEN** the user clicks Next or Prev song during boardless Play mode after elapsed playback time has already passed
- **THEN** the UI SHALL select the adjacent song
- **AND** the UI SHALL recalculate the manual playback offset so the effective playback position points at the selected song
- **AND** later elapsed-time updates SHALL keep using that corrected effective playback position
