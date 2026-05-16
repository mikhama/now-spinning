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
When a `scan` event is received with a valid `record_id`, the UI SHALL transition to standby mode showing that record. When `record_id` is null, the UI SHALL show the NFC error state. When `record_id` refers to a non-existent record, the UI SHALL show the not-found state.

#### Scenario: Scan with valid record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists
- **THEN** the mode SHALL change to "standby" with `currentRecordId` set to "1" and no error state

#### Scenario: Scan with null record_id
- **WHEN** a `scan` event is received with `{"record_id": null}`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "nfc"

#### Scenario: Scan with unknown record_id
- **WHEN** a `scan` event is received with `{"record_id": "999"}` and record "999" does not exist
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"

### Requirement: Play/stop status events
When a `status` event with `status: "play"` is received, the UI SHALL transition to play mode. When `status: "stop"` is received, the UI SHALL transition to standby mode.

#### Scenario: Status play event
- **WHEN** a `status` event is received with `{"status": "play"}`
- **THEN** the mode SHALL change to "play"

#### Scenario: Status stop event
- **WHEN** a `status` event is received with `{"status": "stop"}`
- **THEN** the mode SHALL change to "standby"

### Requirement: Link error event
When a `link_error` event is received, the UI SHALL show the link error state in the current link or re-link mode.

#### Scenario: Link error during link mode
- **WHEN** the mode is "link" and a `link_error` event is received
- **THEN** `linkError` SHALL be set to true and the UI SHALL render the error display
