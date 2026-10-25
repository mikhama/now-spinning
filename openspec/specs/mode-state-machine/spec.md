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
When a `scan` event is received with a non-null `record_id` that resolves to a linked record, the UI SHALL transition to standby mode showing that record. When `record_id` refers to a non-existent or unlinked record, the UI SHALL show the not-found state. A scan of a different linked record SHALL reset the visible side and track to the first side and track. A scan of the same linked record SHALL preserve its selected side. The UI SHALL show the NFC error state for a null scan only before any successful non-null scan or valid `current_record` has established a record during the running program. Once a non-null scan has resolved a view, a later null scan SHALL leave the current mode, record or not-found view, selected side and track, and playback timing unchanged. Real NFC polling SHALL occur only in Standby; a null scan received during Playing can only come from an external event source.

#### Scenario: Scan with a newly selected linked record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists with `linked: true` and is different from the current record
- **THEN** the mode SHALL change to "standby" with `currentRecordId` set to "1" and no error state
- **AND** `currentSideIndex` SHALL be `0`
- **AND** `currentTrackIndex` SHALL be `0`

#### Scenario: Same linked record is scanned again
- **WHEN** linked record "1" is selected on side B
- **AND** a `scan` event is received with `{"record_id": "1"}`
- **THEN** the mode SHALL change to "standby" with `currentRecordId` set to "1" and no error state
- **AND** the selected side SHALL remain B

#### Scenario: Externally supplied null scan after a valid record in Standby
- **WHEN** linked record "1" is selected on side B in Standby
- **AND** an external event source supplies a `scan` event with `{"record_id": null}`
- **THEN** the mode SHALL remain "standby" with record "1" and Side B visible
- **AND** `standbyError`, `currentRecordId`, `currentSideIndex`, and `currentTrackIndex` SHALL remain unchanged

#### Scenario: Externally supplied null scan after a valid record in Playing
- **WHEN** linked record "1" is selected in Playing with a playback time and selected side and track
- **AND** an external event source supplies a `scan` event with `{"record_id": null}`
- **THEN** the mode SHALL remain "play"
- **AND** the record, playback time, selected side, and selected track SHALL remain unchanged

#### Scenario: Scan with null record_id before a valid record
- **WHEN** no successful scan or valid `current_record` has established a record and a `scan` event is received with `{"record_id": null}`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "nfc"
- **AND** `currentRecordId` SHALL remain `null`

#### Scenario: Repeated startup null scan
- **WHEN** a null scan has already shown the startup NFC error and no successful scan has occurred
- **AND** another null scan is received
- **THEN** the UI SHALL keep the existing NFC error state without another transition

#### Scenario: Startup error does not reappear after leaving it
- **WHEN** a startup null scan has already shown the NFC error and the user switches to another mode
- **AND** another null scan is received before any successful scan
- **THEN** the UI SHALL remain in the selected mode and SHALL NOT show the NFC error again

#### Scenario: Same linked record recovers after NFC error
- **WHEN** a startup null scan showed the NFC error
- **AND** a later `scan` event is received with `{"record_id": "1"}` for a linked record
- **THEN** the NFC error state SHALL clear and the record SHALL be shown in Standby

#### Scenario: Valid current record recovers startup NFC error
- **WHEN** a startup null scan showed the NFC error
- **AND** a valid `current_record` event establishes linked record "1"
- **THEN** the NFC error state SHALL clear and record "1" SHALL be shown in Standby

#### Scenario: Scan with unknown record_id
- **WHEN** a `scan` event is received with `{"record_id": "999"}` and record "999" does not exist
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"
- **AND** `currentRecordId` SHALL be `null`

#### Scenario: Scan with unlinked record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists with `linked: false`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"
- **AND** `currentRecordId` SHALL be `null`

#### Scenario: External null scan after unknown or unlinked scan
- **WHEN** a successful non-null scan selected the Record Not Found view
- **AND** a later externally supplied null scan is received
- **THEN** the UI SHALL keep the Record Not Found view and SHALL NOT show NFC Reading Error

### Requirement: Play/stop status events
When a `status` event with `status: "play"` is received, the UI SHALL transition to play mode without synthesizing a fallback record. If that play event includes a `time` field formatted as `MM:SS`, the UI SHALL store that exact value as the current playback time for Play mode, parse it as the latest boardless elapsed playback time, and treat the turntable as spinning. The UI SHALL NOT store a separate `spinning` payload field. When `status: "stop"` is received, the UI SHALL transition to standby mode while preserving the current record or standby error context and clearing stored Play-only timing state. If playback stops after at least 60 seconds of raw elapsed playback, or at or after 20 seconds before the selected side end when that side has a positive estimated duration, including any overrun, the selected side SHALL advance to the next side before Play-only timing state is cleared. A stop that satisfies neither condition SHALL keep the selected side.
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

#### Scenario: Status stop after one minute advances side
- **WHEN** a `status` event with `{"status": "stop"}` is received after raw elapsed playback reached `01:00`
- **AND** the effective playback position is earlier than the final 20 seconds of the selected side
- **THEN** the selected side SHALL advance once to the next side with wraparound
- **AND** the selected song SHALL reset to the first song on that side

#### Scenario: Brief stop before side end keeps side
- **WHEN** a `status` event with `{"status": "stop"}` is received after less than 60 seconds of raw elapsed playback
- **AND** the effective playback position is earlier than the final 20 seconds of a side with a positive estimated duration
- **THEN** the selected side SHALL remain unchanged

#### Scenario: Missing side duration uses one-minute rule
- **WHEN** the selected side has no positive estimated duration
- **AND** a `status` event with `{"status": "stop"}` is received after less than 60 seconds of raw elapsed playback
- **THEN** the selected side SHALL remain unchanged

### Requirement: Boardless playback correction state
During boardless Play mode, the UI mode state SHALL maintain enough timing state to combine server elapsed time with user side and song corrections. The effective playback position SHALL be recalculated whenever a boardless play status event, Side button click, Prev song click, or Next song click changes playback selection. Prev and Next song clicks SHALL keep the selected side unchanged and wrap the song selection within that side.

#### Scenario: Manual side correction stores offset
- **WHEN** the user manually changes from side "A" to side "B" while the latest server elapsed time is `01:00`
- **THEN** the selected side SHALL become side "B"
- **AND** the manual playback correction offset SHALL be set so the effective playback position is at side "B" for subsequent elapsed-time updates

#### Scenario: Manual song correction stores offset
- **WHEN** the user manually changes from the first song to the second song while the latest server elapsed time is `01:00`
- **THEN** the selected song SHALL become the second song
- **AND** the manual playback correction offset SHALL be set so the effective playback position is at the selected song for subsequent elapsed-time updates

#### Scenario: Manual song wrap corrects playback position on the same side
- **WHEN** the user clicks Next on the final song or Prev on the first song of the selected side during Play
- **THEN** the selected song SHALL wrap to the opposite end of the same side
- **AND** the selected side SHALL remain unchanged
- **AND** the manual playback correction offset SHALL point to the newly selected song's start for subsequent elapsed-time updates

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
The system SHALL perform real NFC scan polling only while the current UI mode is standby, including standby fallback states represented by standby errors. The coordinator SHALL default to a 200 ms detection timeout and retain a 500 ms RF-off pause after each operation, including successful record identification. Hardware commands SHALL remain serialized in the NFC worker. Entering a non-scanning mode SHALL prevent further standby scans; an already claimed operation SHALL finish bounded processing and RF-off cleanup before the worker becomes idle. Mode-change handlers SHALL NOT send hardware commands.

#### Scenario: Standby mode polls for NFC tag
- **WHEN** the current UI mode is standby
- **THEN** the system SHALL check for an NFC tag using at most 200 ms per detection probe with a 500 ms RF-off pause after each operation
- **AND** it SHALL confirm RF-off before the 500 ms pause after the operation

#### Scenario: Non-standby mode does not poll
- **WHEN** the current UI mode is sync, link, re-link, stylus, or play
- **THEN** the system SHALL NOT perform standby NFC tag checks
- **AND** RF SHALL remain off unless an explicitly requested NFC operation is active

#### Scenario: Standby error state remains polling-eligible
- **WHEN** the current UI mode is standby with `standbyError` set to `not-found` or `nfc`
- **THEN** the system SHALL treat the state as standby for NFC polling eligibility

#### Scenario: Mode changes during active standby attempt
- **WHEN** a standby attempt is already active and the mode changes to a non-scanning mode
- **THEN** the worker SHALL finish the bounded operation and RF-off cleanup before becoming idle
- **AND** it SHALL NOT start another standby attempt while that mode remains active
- **AND** it SHALL discard a late scan result or error event that would return the UI to Standby

### Requirement: Standby NFC scan events preserve last valid record
During standby NFC polling, the system SHALL track the last successfully decoded record ID for duplicate suppression and SHALL broadcast a scan event when the decoded ID changes. Before any successful read, it SHALL broadcast at most one null scan for NFC read failures, including when no-card polls occur between failures. After any successful read, NFC read failures SHALL NOT broadcast null scans or clear the last emitted record ID. The frontend SHALL keep the state resolved from the last scan when a tag leaves the field or a later read fails.

#### Scenario: First successful standby scan is emitted
- **WHEN** standby NFC polling reads record id `1` and no record id has been emitted yet
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`

#### Scenario: Successful unlinked standby scan preserves its ID
- **WHEN** standby NFC polling successfully reads record id `1`
- **AND** record id `1` is not linked
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`
- **AND** the frontend SHALL show the standby record-not-found state
- **AND** the frontend SHALL NOT show the standby NFC error state

#### Scenario: Same record remains in field
- **WHEN** standby NFC polling reads record id `1` after record id `1` was already emitted
- **THEN** the system SHALL NOT broadcast another scan event

#### Scenario: Tag leaves field after valid scan
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later poll detects no card in the field
- **THEN** the system SHALL NOT broadcast a scan event
- **AND** the frontend SHALL continue showing the state resolved from record id `1`

#### Scenario: No tag before any valid scan
- **WHEN** standby NFC polling detects no card before any successful scan has occurred
- **THEN** the system SHALL NOT broadcast a scan event

#### Scenario: Different record is scanned
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later successful poll reads record id `2`
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"2"}}`

#### Scenario: First startup NFC read error is emitted
- **WHEN** standby NFC polling encounters an NFC read error before any successful tag read
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":null}}`
- **AND** the frontend SHALL show the standby NFC error state

#### Scenario: Repeated startup read errors with no-card polls
- **WHEN** an NFC read error has already been emitted before any successful read
- **AND** subsequent polls report read errors or no card
- **THEN** the system SHALL NOT broadcast another scan event

#### Scenario: First successful read recovers from startup error
- **WHEN** standby NFC polling emitted a startup null scan
- **AND** a later successful poll reads record id `1`, with or without intervening no-card polls
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`
- **AND** the frontend SHALL resolve record id `1` instead of retaining the standby NFC error state

#### Scenario: Read error after a successful scan
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later NFC read fails
- **THEN** the system SHALL NOT broadcast a null scan
- **AND** a later successful read of record id `1` SHALL remain suppressed as a duplicate

#### Scenario: No-card is not an error
- **WHEN** standby NFC polling detects no card in the field
- **THEN** the system SHALL NOT broadcast `{"event":"scan","data":{"record_id":null}}`

### Requirement: Real scan event payloads match boardless scan events
Real NFC standby scan broadcasts SHALL use the same event names and payload shapes as boardless scan events. A real NFC error payload SHALL be sent only once before the first successful NFC read.

#### Scenario: Real scan success payload
- **WHEN** real NFC standby polling reads record id `1`
- **THEN** the frontend SHALL receive `{"event":"scan","data":{"record_id":"1"}}`

#### Scenario: Real startup scan error payload
- **WHEN** real NFC standby polling reports the first NFC read error before any successful read
- **THEN** the frontend SHALL receive `{"event":"scan","data":{"record_id":null}}`

### Requirement: Inactive modes keep NFC RF off
Play, Sync, Stylus, idle Link/Re-link, and every other mode without an active NFC operation SHALL keep RF off. Link/Re-link SHALL enable RF only for explicitly requested writes and their bounded probes, keep RF off between probes and after completion, and SHALL serialize writes with reads in the worker. Duplicate suppression, record replacement, last-record retention and event formats SHALL remain unchanged.

#### Scenario: Idle inactive modes
- **WHEN** Play, Sync, Stylus, Link/Re-link, or an unknown mode has no active NFC operation
- **THEN** RF SHALL remain off and no new standby probe SHALL begin

#### Scenario: Explicit Link or Re-link write
- **WHEN** an explicit write is requested in Link or Re-link
- **THEN** only the NFC worker SHALL execute it, using bounded RF-on probes and RF-off pauses
- **AND** RF SHALL be off after the complete write or any failure
