## ADDED Requirements

### Requirement: Link and re-link write only after button click
The system SHALL start real NFC write readiness for a link or re-link workflow only after the user clicks the Link or Re-Link button for the selected record.

#### Scenario: Enter link mode does not start writing
- **WHEN** the user enters link mode and a record is selected
- **THEN** the system SHALL NOT wait for a tag to write until the user clicks the Link button

#### Scenario: Enter re-link mode does not start writing
- **WHEN** the user enters re-link mode and a record is selected
- **THEN** the system SHALL NOT wait for a tag to write until the user clicks the Re-Link button

#### Scenario: Link button starts write readiness
- **WHEN** the user clicks the Link button for selected record id `1`
- **THEN** the system SHALL wait for a physical NFC tag to enter the field
- **AND** the system SHALL attempt to write exactly `1` to that tag

#### Scenario: Re-Link button starts write readiness
- **WHEN** the user clicks the Re-Link button for selected record id `1`
- **THEN** the system SHALL wait for a physical NFC tag to enter the field
- **AND** the system SHALL attempt to write exactly `1` to that tag

### Requirement: Link and re-link real NFC outcomes use boardless event shapes
Real NFC link and re-link writes SHALL notify the frontend only for terminal write outcomes, using the same event names and payload shapes as boardless link result events.

#### Scenario: Link write succeeds
- **WHEN** a real NFC Link write successfully stores selected record id `1` on a tag
- **THEN** the system SHALL broadcast `{"event":"link_success","data":{"record_id":"1"}}`

#### Scenario: Re-Link write succeeds
- **WHEN** a real NFC Re-Link write successfully stores selected record id `1` on a tag
- **THEN** the system SHALL broadcast `{"event":"link_success","data":{"record_id":"1"}}`

#### Scenario: Link write fails
- **WHEN** a real NFC Link write fails for selected record id `1`
- **THEN** the system SHALL broadcast `{"event":"link_error","data":{"record_id":"1"}}`

#### Scenario: Re-Link write fails
- **WHEN** a real NFC Re-Link write fails for selected record id `1`
- **THEN** the system SHALL broadcast `{"event":"link_error","data":{"record_id":"1"}}`

#### Scenario: No intermediate link events
- **WHEN** the system is waiting for a tag after the user clicks Link or Re-Link
- **THEN** the system SHALL NOT broadcast a link or re-link event until the write succeeds or fails
