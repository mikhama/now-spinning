## ADDED Requirements

### Requirement: Database updates record linked state
The database layer SHALL provide a function for setting a record's linked state by record ID. The function SHALL set `linked = 1` when linking succeeds and SHALL report whether a matching row was updated.

#### Scenario: Update existing record linked state
- **WHEN** the database contains record "1" with `linked = 0`
- **AND** the linked-state update function is called for record "1"
- **THEN** record "1" SHALL be stored with `linked = 1`
- **AND** the function SHALL report that a row was updated

#### Scenario: Update missing record linked state
- **WHEN** the database does not contain record "999"
- **AND** the linked-state update function is called for record "999"
- **THEN** no record SHALL be changed
- **AND** the function SHALL report that no row was updated
