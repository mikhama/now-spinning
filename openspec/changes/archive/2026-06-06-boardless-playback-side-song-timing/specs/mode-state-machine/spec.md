## MODIFIED Requirements

### Requirement: Play/stop status events
When a `status` event with `status: "play"` is received, the UI SHALL transition to play mode without synthesizing a fallback record. If that play event includes a `time` field formatted as `MM:SS`, the UI SHALL store that exact value as the current playback time for Play mode, parse it as the latest boardless elapsed playback time, and treat the turntable as spinning. The UI SHALL NOT store a separate `spinning` payload field. When `status: "stop"` is received, the UI SHALL transition to standby mode while preserving the current record or standby error context and clearing stored Play-only timing state. If playback stops at or after 20 seconds before the selected side end, including any overrun beyond the estimated side length, the selected side SHALL advance to the next side before Play-only timing state is cleared.
The selected song SHALL reset to the first song on the selected side when playback stops, so a later `status: "play"` for the same record starts from the selected side start rather than preserving a prior song correction.

#### Scenario: Status play event with active record
- **WHEN** a `status` event is received with `{"status": "play", "time": "00:01"}` and `currentRecordId` points to an existing record
- **THEN** the mode SHALL change to `"play"`
- **AND** `currentRecordId` SHALL remain set to that record
- **AND** the stored playback time SHALL be `"00:01"`
- **AND** the latest boardless elapsed playback time SHALL be one second

#### Scenario: Status play event without active record
- **WHEN** a `status` event is received with `{"status": "play", "time": "00:01"}` and no current record is active because the latest scan resolved to record-not-found
- **THEN** the mode SHALL change to `"play"`
- **AND** `currentRecordId` SHALL remain `null`
- **AND** the stored playback time SHALL be `"00:01"`
- **AND** the event handling SHALL NOT assign a default or fallback record

#### Scenario: Status play event derives spinning state
- **WHEN** a `status` event is received with `{"status": "play", "time": "03:30"}`
- **THEN** the mode SHALL change to `"play"`
- **AND** the turntable SHALL be treated as spinning
- **AND** no separate `spinning` payload value SHALL be stored

#### Scenario: Status stop event preserves fallback context
- **WHEN** a `status` event is received with `{"status": "stop"}` after play mode was entered without a valid current record
- **THEN** the mode SHALL change to `"standby"`
- **AND** `currentRecordId` SHALL remain `null`
- **AND** `standbyError` SHALL remain `"not-found"`
- **AND** the stored playback time SHALL be cleared
- **AND** boardless elapsed playback time and manual playback correction offset SHALL be cleared
- **AND** the selected song SHALL reset to the first song on the selected side

#### Scenario: Status stop near or after side end advances side
- **WHEN** a `status` event with `{"status": "stop"}` is received while the effective playback position is at or after 20 seconds before the selected side end
- **THEN** the mode SHALL change to `"standby"`
- **AND** the selected side SHALL advance to the next side with wraparound
- **AND** the selected song SHALL reset to the first song on the advanced side
- **AND** Play-only timing state SHALL be cleared

#### Scenario: Status stop after side overrun advances side
- **WHEN** a `status` event with `{"status": "stop"}` is received while the effective playback position is beyond the selected side end
- **THEN** the mode SHALL change to `"standby"`
- **AND** the selected side SHALL advance to the next side with wraparound
- **AND** the selected song SHALL reset to the first song on the advanced side
- **AND** Play-only timing state SHALL be cleared

## ADDED Requirements

### Requirement: Boardless playback correction state
During boardless Play mode, the UI mode state SHALL maintain enough timing state to combine server elapsed time with user side and song corrections. The effective playback position SHALL be recalculated whenever a boardless play status event, Side button click, Prev song click, or Next song click changes playback selection.

#### Scenario: Manual side correction stores offset
- **WHEN** the user manually changes from side "A" to side "B" while the latest server elapsed time is `01:00`
- **THEN** the selected side SHALL become side "B"
- **AND** the manual playback correction offset SHALL be set so the effective playback position is at side "B" for subsequent elapsed-time updates

#### Scenario: Manual song correction stores offset
- **WHEN** the user manually changes from the first song to the second song while the latest server elapsed time is `01:00`
- **THEN** the selected song SHALL become the second song
- **AND** the manual playback correction offset SHALL be set so the effective playback position is at the selected song for subsequent elapsed-time updates

#### Scenario: Stopped playback clears manual song correction
- **WHEN** the user manually selected the second song during Play mode
- **AND** a `status` event with `{"status": "stop"}` is received
- **THEN** the selected song SHALL reset to the first song on the selected side
- **AND** a later `status: "play"` for the same record SHALL start from the selected side's first song

#### Scenario: New scan resets playback correction state
- **WHEN** a valid scan event loads a new current record
- **THEN** the selected side SHALL reset to the first side
- **AND** the selected track SHALL reset to the first track
- **AND** boardless elapsed playback time and manual playback correction offset SHALL be cleared

#### Scenario: Same-record play preserves manually selected side
- **WHEN** the user manually selects side "B" for the current record before a `status: "play"` event arrives
- **THEN** the selected side SHALL remain side "B" after Play mode starts
- **AND** the manual playback correction offset SHALL be set from side "B"
- **AND** the selected song SHALL be the first song unless a song was manually selected before Play mode starts
