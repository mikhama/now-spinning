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
When a `status` event with `status: "play"` is received, the UI SHALL transition to play mode without synthesizing a fallback record. When `status: "stop"` is received, the UI SHALL transition to standby mode while preserving the current record or standby error context.

#### Scenario: Status play event with active record
- **WHEN** a `status` event is received with `{"status": "play"}` and `currentRecordId` points to an existing record
- **THEN** the mode SHALL change to `"play"`
- **AND** `currentRecordId` SHALL remain set to that record

#### Scenario: Status play event without active record
- **WHEN** a `status` event is received with `{"status": "play"}` and no current record is active because the latest scan resolved to record-not-found
- **THEN** the mode SHALL change to `"play"`
- **AND** `currentRecordId` SHALL remain `null`
- **AND** the event handling SHALL NOT assign a default or fallback record

#### Scenario: Status stop event preserves fallback context
- **WHEN** a `status` event is received with `{"status": "stop"}` after play mode was entered without a valid current record
- **THEN** the mode SHALL change to `"standby"`
- **AND** `currentRecordId` SHALL remain `null`
- **AND** `standbyError` SHALL remain `"not-found"`

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

