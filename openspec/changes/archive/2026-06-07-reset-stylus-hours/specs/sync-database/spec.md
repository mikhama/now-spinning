## ADDED Requirements

### Requirement: Database resets stylus hours
The database layer SHALL provide an operation that resets an existing stylus row by setting `distance_hours` to `0`.

#### Scenario: Reset existing stylus hours
- **WHEN** the reset operation is called for an existing stylus ID
- **THEN** the database SHALL update that stylus row with `distance_hours` equal to `0`
- **AND** the operation SHALL report that a row was updated

#### Scenario: Reset missing stylus hours
- **WHEN** the reset operation is called for a stylus ID that does not exist
- **THEN** the database SHALL leave existing rows unchanged
- **AND** the operation SHALL report that no row was updated
