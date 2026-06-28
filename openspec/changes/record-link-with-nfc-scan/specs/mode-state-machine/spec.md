## ADDED Requirements

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
