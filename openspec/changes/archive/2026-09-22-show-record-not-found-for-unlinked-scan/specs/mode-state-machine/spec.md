## MODIFIED Requirements

### Requirement: Scan event transitions to standby
When a `scan` event is received with a non-null `record_id` that resolves to a linked record, the UI SHALL transition to standby mode showing that record. When `record_id` is null, the UI SHALL show the NFC error state. When `record_id` refers to a non-existent or unlinked record, the UI SHALL show the not-found state. Scan events that load a linked record SHALL reset the visible side to the first side and the visible track index to the first track.

#### Scenario: Scan with linked record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists with `linked: true`
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

#### Scenario: Scan with unlinked record_id
- **WHEN** a `scan` event is received with `{"record_id": "1"}` and record "1" exists with `linked: false`
- **THEN** the mode SHALL change to "standby" with `standbyError` set to "not-found"
- **AND** `currentRecordId` SHALL be `null`

### Requirement: Standby NFC scan events preserve last valid record
During standby NFC polling, the system SHALL track the last successfully decoded record ID for duplicate suppression and SHALL broadcast scan events when the decoded ID changes, an NFC read error occurs, or a successful scan recovers from an emitted NFC read error. The frontend SHALL keep the state resolved from the last scan when a tag leaves the field.

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
- **WHEN** standby NFC polling reads record id `1` after record id `1` was already emitted without an intervening NFC read error
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

#### Scenario: NFC read error is emitted
- **WHEN** standby NFC polling encounters an NFC read error
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":null}}`
- **AND** the frontend SHALL show the standby NFC error state

#### Scenario: Same record recovers after NFC read error
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later NFC read error caused `{"event":"scan","data":{"record_id":null}}` to be emitted
- **AND** a later successful poll reads record id `1`, with or without intervening no-card polls
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`
- **AND** the frontend SHALL resolve record id `1` instead of retaining the standby NFC error state

#### Scenario: No-card is not an error
- **WHEN** standby NFC polling detects no card in the field
- **THEN** the system SHALL NOT broadcast `{"event":"scan","data":{"record_id":null}}`
