## MODIFIED Requirements

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
