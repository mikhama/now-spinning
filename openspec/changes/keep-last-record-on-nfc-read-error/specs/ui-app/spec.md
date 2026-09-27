## MODIFIED Requirements

### Requirement: Standby mode — NFC Reading Error
In Standby mode, the UI SHALL display a gray cover placeholder with "NFC Reading Error" text centered inside it only when an NFC reading error occurs before the program has resolved any successful tag scan or established a valid current record. After a successful scan, a later NFC reading error SHALL leave the resolved Standby record or Record Not Found view unchanged.

#### Scenario: Startup NFC reading error in Standby
- **WHEN** the mode is Standby and an NFC reading error occurs before any successful scan or valid current record
- **THEN** the UI SHALL show a cover placeholder with "NFC Reading Error" text inside

#### Scenario: Valid current record replaces startup NFC error
- **WHEN** Standby shows the NFC Reading Error placeholder
- **AND** a valid `current_record` event establishes a linked record
- **THEN** the record cover, metadata, and Side button SHALL replace the placeholder

#### Scenario: NFC reading error after a linked record is shown
- **WHEN** Standby shows a linked record with its cover, metadata, and Side button
- **AND** an NFC reading error occurs
- **THEN** the same record, side, and Side button SHALL remain visible
- **AND** the UI SHALL NOT show the NFC Reading Error placeholder

#### Scenario: NFC reading error after Record Not Found
- **WHEN** Standby shows Record Not Found for a successful scan of an unknown or unlinked ID
- **AND** an NFC reading error occurs
- **THEN** Record Not Found SHALL remain visible
- **AND** the UI SHALL NOT show the NFC Reading Error placeholder
