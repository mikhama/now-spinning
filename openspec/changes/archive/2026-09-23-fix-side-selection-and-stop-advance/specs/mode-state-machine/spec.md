## MODIFIED Requirements

### Requirement: Scan event transitions to standby
When a `scan` event is received with a non-null `record_id` that resolves to a linked record, the UI SHALL transition to standby mode showing that record. When `record_id` is null, the UI SHALL show the NFC error state. When `record_id` refers to a non-existent or unlinked record, the UI SHALL show the not-found state. A scan of a different linked record SHALL reset the visible side and track to the first side and track. A scan of the same linked record SHALL preserve its selected side, including after a transient NFC read error. A null scan SHALL show the NFC error state without discarding the last valid record identity or selected side; if no record was active, the current record SHALL remain null.

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

#### Scenario: Scan with null record_id after a valid record
- **WHEN** linked record "1" is selected on side B
- **AND** a `scan` event is received with `{"record_id": null}`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "nfc"
- **AND** the record display and Side button SHALL be hidden
- **AND** `currentRecordId` SHALL remain "1" and the selected side SHALL remain B

#### Scenario: Scan with null record_id before a valid record
- **WHEN** no record is active and a `scan` event is received with `{"record_id": null}`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "nfc"
- **AND** `currentRecordId` SHALL remain `null`

#### Scenario: Same linked record recovers after NFC error
- **WHEN** linked record "1" was selected on side B before a null scan
- **AND** a later `scan` event is received with `{"record_id": "1"}`
- **THEN** the NFC error state SHALL clear and the record SHALL be shown in Standby
- **AND** side B SHALL remain selected

#### Scenario: Scan with unknown record_id
- **WHEN** a `scan` event is received with `{"record_id": "999"}` and record "999" does not exist
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"
- **AND** `currentRecordId` SHALL be `null`

#### Scenario: Scan with unlinked record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists with `linked: false`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"
- **AND** `currentRecordId` SHALL be `null`

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

