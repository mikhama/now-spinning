## ADDED Requirements

### Requirement: Database provides active stylus lookup
The database layer SHALL provide an operation that returns the active stylus row with its current `distance_hours` value.

#### Scenario: Active stylus exists
- **WHEN** the database contains a stylus row with `active = 1`
- **THEN** the active stylus lookup SHALL return that stylus ID and current `distance_hours`

#### Scenario: No active stylus exists
- **WHEN** the database contains no stylus rows
- **THEN** the active stylus lookup SHALL return no stylus

### Requirement: Database increments stylus hours
The database layer SHALL provide an operation that increments an existing stylus row's `distance_hours` by a supplied hour delta.

#### Scenario: Increment existing stylus hours
- **WHEN** the database contains stylus "1" with `distance_hours = 100.0`
- **AND** the increment operation is called for stylus "1" with delta `0.25`
- **THEN** stylus "1" SHALL be stored with `distance_hours = 100.25`
- **AND** the operation SHALL report that a row was updated

#### Scenario: Increment missing stylus hours
- **WHEN** the database does not contain stylus "999"
- **AND** the increment operation is called for stylus "999"
- **THEN** no stylus row SHALL be changed
- **AND** the operation SHALL report that no row was updated

### Requirement: Database commits stylus-hour writes durably
The database layer SHALL configure SQLite connections used for committed stylus-hour writes with explicit local durability settings.

#### Scenario: Connection uses durable synchronous setting
- **WHEN** the database layer opens a SQLite connection for stylus-hour persistence
- **THEN** the connection SHALL use WAL journal mode
- **AND** the connection SHALL set a synchronous mode suitable for durable committed writes

#### Scenario: Committed increment survives new connection
- **WHEN** the increment operation commits a stylus-hour delta
- **AND** a new database connection reads the same stylus row
- **THEN** the new connection SHALL observe the incremented `distance_hours` value
