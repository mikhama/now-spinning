## MODIFIED Requirements

### Requirement: Standby mode — record display
In Standby mode, the UI SHALL display the current record's cover image, catalogue number (#ID), artist, and title only when a current record has been established by runtime state. A Side button SHALL show the current side label and allow switching sides. When a newly loaded record has sides, the initial displayed side SHALL be the first side and SHALL render as "Side A" when the first side label is "A".

#### Scenario: Record is available in Standby
- **WHEN** the mode is Standby and a valid current record has been loaded after a scan or runtime event
- **THEN** the UI SHALL show the cover image, "#<id>", artist name, album title, and a Side button

#### Scenario: Initial side label in Standby
- **WHEN** the mode is Standby and a newly loaded record has sides beginning with side id "A"
- **THEN** the Side button SHALL initially display "Side A"

#### Scenario: Side button in Standby
- **WHEN** the user clicks the Side button in Standby
- **THEN** the UI SHALL cycle to the next side and update the button label

### Requirement: Standby mode — Record Not Found
In Standby mode, when a scanned record is not found in the database, or when the app has just loaded before any record scan has succeeded, the UI SHALL display a gray cover placeholder with "Record Not Found" text centered inside it.

#### Scenario: Record not found in Standby
- **WHEN** the mode is Standby and the scanned record is not in the database
- **THEN** the UI SHALL show a cover placeholder with "Record Not Found" text inside

#### Scenario: Startup before first scan
- **WHEN** the app loads with no URL hash and no successful scan has happened yet
- **THEN** the standby view SHALL show the same "Record Not Found" placeholder instead of record metadata