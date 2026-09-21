## MODIFIED Requirements

### Requirement: Standby NFC scan events preserve last valid record
During standby NFC polling, the system SHALL keep the last successfully scanned record id as the record ready to play when a tag leaves the field, and SHALL broadcast scan events when the scanned record changes, an NFC read error occurs, or a successful scan recovers from an emitted NFC read error.

#### Scenario: First successful standby scan is emitted
- **WHEN** standby NFC polling reads record id `1` and no record id has been emitted yet
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`

#### Scenario: Same record remains in field
- **WHEN** standby NFC polling reads record id `1` after record id `1` was already emitted without an intervening NFC read error
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

#### Scenario: Same record recovers after NFC read error
- **WHEN** standby NFC polling previously emitted record id `1`
- **AND** a later NFC read error caused `{"event":"scan","data":{"record_id":null}}` to be emitted
- **AND** a later successful poll reads record id `1`, with or without intervening no-card polls
- **THEN** the system SHALL broadcast `{"event":"scan","data":{"record_id":"1"}}`
- **AND** the frontend SHALL show record id `1` instead of the standby NFC error state

#### Scenario: No-card is not an error
- **WHEN** standby NFC polling detects no card in the field
- **THEN** the system SHALL NOT broadcast `{"event":"scan","data":{"record_id":null}}`
