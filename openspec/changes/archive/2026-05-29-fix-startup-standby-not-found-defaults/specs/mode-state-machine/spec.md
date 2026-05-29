## ADDED Requirements

### Requirement: Initial load defaults to standby not-found before scan
When the UI initializes without a URL hash, it SHALL start in standby mode with no active record selected and the standby not-found state visible.

#### Scenario: Cold load without hash
- **WHEN** the app loads at the root URL with no hash and before any runtime event has selected a record
- **THEN** the mode SHALL be "standby"
- **AND** `currentRecordId` SHALL be `null`
- **AND** `standbyError` SHALL be "not-found"

## MODIFIED Requirements

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