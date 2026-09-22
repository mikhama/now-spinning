## MODIFIED Requirements

### Requirement: Standby mode — Record Not Found
In Standby mode, when a scanned record is not found in the database, when the scanned record exists but is not linked, or when the app has just loaded before any record scan has succeeded, the UI SHALL display a gray cover placeholder with "Record Not Found" text centered inside it. An unlinked scan SHALL NOT activate that record's metadata.

#### Scenario: Record not found in Standby
- **WHEN** the mode is Standby and the scanned record is not in the database
- **THEN** the UI SHALL show a cover placeholder with "Record Not Found" text inside

#### Scenario: Unlinked record scanned in Standby
- **WHEN** the mode is Standby and the scanned record exists with `linked: false`
- **THEN** the UI SHALL show a cover placeholder with "Record Not Found" text inside
- **AND** the UI SHALL NOT show the scanned record's metadata
- **AND** the UI SHALL NOT show the "NFC Reading Error" placeholder

#### Scenario: Startup before first scan
- **WHEN** the app loads with no URL hash and no successful scan has happened yet
- **THEN** the standby view SHALL show the same "Record Not Found" placeholder instead of record metadata
