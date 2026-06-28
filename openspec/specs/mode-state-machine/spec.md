# mode-state-machine Specification

## Purpose
UI mode transition logic driven by button presses and WebSocket events.
## Requirements
### Requirement: Mode button cycle order
The mode button SHALL cycle through modes in this fixed order: standby → sync → link → re-link → stylus → standby. Play mode SHALL NOT be reachable via the mode button. Error sub-states (standby-not-found, standby-error, link-error, stylus with no styli) SHALL be treated as their parent mode for cycle purposes.

#### Scenario: Mode button from standby
- **WHEN** the current mode is "standby" and the mode button is pressed
- **THEN** the mode SHALL change to "sync"

#### Scenario: Mode button from sync
- **WHEN** the current mode is "sync" and the mode button is pressed
- **THEN** the mode SHALL change to "link"

#### Scenario: Mode button from link
- **WHEN** the current mode is "link" and the mode button is pressed
- **THEN** the mode SHALL change to "re-link"

#### Scenario: Mode button from re-link
- **WHEN** the current mode is "re-link" and the mode button is pressed
- **THEN** the mode SHALL change to "stylus"

#### Scenario: Mode button from stylus
- **WHEN** the current mode is "stylus" and the mode button is pressed
- **THEN** the mode SHALL change to "standby"

#### Scenario: Mode button from standby-not-found
- **WHEN** the current mode is "standby" with standbyError "not-found" and the mode button is pressed
- **THEN** the mode SHALL change to "sync"

#### Scenario: Mode button from play mode
- **WHEN** the current mode is "play" and the mode button is pressed
- **THEN** the mode SHALL change to "standby"

### Requirement: Scan event transitions to standby
When a `scan` event is received with a valid `record_id`, the UI SHALL transition to standby mode showing that record. When `record_id` is null, the UI SHALL show the NFC error state. When `record_id` refers to a non-existent record, the UI SHALL show the not-found state. Scan events that load a valid record SHALL reset the visible side to the first side and the visible track index to the first track.

#### Scenario: Scan with valid record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists
- **THEN** the mode SHALL change to "standby" with `currentRecordId` set to "1" and no error state
- **AND** `currentSideIndex` SHALL be `0`
- **AND** `currentTrackIndex` SHALL be `0`

#### Scenario: Scan with null record_id
- **WHEN** a `scan` event is received with `{"record_id": null}`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "nfc"
- **AND** `currentRecordId` SHALL be `null`

#### Scenario: Scan with unknown record_id
- **WHEN** a `scan` event is received with `{"record_id": "999"}` and record "999" does not exist
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"
- **AND** `currentRecordId` SHALL be `null`

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
- **WHEN** a `status` event is received with `{"status": "play", "time":"03:30"}`
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

### Requirement: Link error event
When a `link_error` event is received, the UI SHALL show the link error state in the current link or re-link mode.

#### Scenario: Link error during link mode
- **WHEN** the mode is "link" and a `link_error` event is received
- **THEN** `linkError` SHALL be set to true and the UI SHALL render the error display

### Requirement: Initial load defaults to standby not-found before scan
When the UI initializes without a URL hash, it SHALL start in standby mode with no active record selected and the standby not-found state visible.

#### Scenario: Cold load without hash
- **WHEN** the app loads at the root URL with no hash and before any runtime event has selected a record
- **THEN** the mode SHALL be "standby"
- **AND** `currentRecordId` SHALL be `null`
- **AND** `standbyError` SHALL be "not-found"

### Requirement: Standby NFC polling runs only in standby
The system SHALL perform real NFC scan polling only while the current UI mode is standby, including standby fallback states represented by standby errors.

#### Scenario: Standby mode polls for NFC tag
- **WHEN** the current UI mode is standby
- **THEN** the system SHALL check for an NFC tag about once per second

#### Scenario: Non-standby mode does not poll
- **WHEN** the current UI mode is sync, link, re-link, stylus, or play
- **THEN** the system SHALL NOT perform the once-per-second standby NFC tag check

#### Scenario: Standby error state remains polling-eligible
- **WHEN** the current UI mode is standby with `standbyError` set to `not-found` or `nfc`
- **THEN** the system SHALL treat the state as standby for NFC polling eligibility

### Requirement: Standby NFC scan events preserve last valid record
During standby NFC polling, the system SHALL keep the last successfully scanned record id as the record ready to play when a tag leaves the field, and SHALL broadcast scan events only when the scanned record changes or an NFC read error occurs.

#### Scenario: First successful standby scan is emitted
- **WHEN** standby NFC polling reads record id `1` and no record id has been emitted yet
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`

#### Scenario: Same record remains in field
- **WHEN** standby NFC polling reads record id `1` after record id `1` was already emitted
- **THEN** the system SHALL NOT broadcast another scan event

#### Scenario: Tag leaves field after valid scan
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later poll detects no card in the field
- **THEN** the system SHALL NOT broadcast a scan event
- **AND** the frontend SHALL continue showing record id `1` as the record ready to play

#### Scenario: No tag before any valid scan
- **WHEN** standby NFC polling detects no card before any successful scan has occurred
- **THEN** the system SHALL NOT broadcast a scan event

#### Scenario: Different record is scanned
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later successful poll reads record id `2`
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"2"}}`

#### Scenario: NFC read error is emitted
- **WHEN** standby NFC polling encounters an NFC read error
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":null}}`
- **AND** the frontend SHALL show the standby NFC error state

#### Scenario: No-card is not an error
- **WHEN** standby NFC polling detects no card in the field
- **THEN** the system SHALL NOT broadcast `{"event":"scan","data":{"record_id":null}}`

### Requirement: Real scan event payloads match boardless scan events
Real NFC standby scan broadcasts SHALL use the same event names and payload shapes as boardless scan events.

#### Scenario: Real scan success payload
- **WHEN** real NFC standby polling reads record id `1`
- **THEN** the frontend SHALL receive `{"event":"scan","data":{"record_id":"1"}}`

#### Scenario: Real scan error payload
- **WHEN** real NFC standby polling reports an NFC read error
- **THEN** the frontend SHALL receive `{"event":"scan","data":{"record_id":null}}`
