# sync-database Specification

## Purpose
SQLite database layer for persisting collection data (styli, records) and tracking sync status.
## Requirements
### Requirement: SQLite database has stylus table
The system SHALL maintain a `stylus` table with the following columns: `id` (TEXT, PRIMARY KEY), `name` (TEXT), `distance_hours` (REAL), `capacity_min_hours` (REAL), `capacity_max_hours` (REAL), `active` (INTEGER, boolean).

#### Scenario: Stylus table schema
- **WHEN** the database is initialized
- **THEN** the `stylus` table SHALL exist with columns: id (TEXT PK), name (TEXT), distance_hours (REAL), capacity_min_hours (REAL), capacity_max_hours (REAL), active (INTEGER)

### Requirement: SQLite database has record table
The system SHALL maintain a `record` table with the following columns: `id` (TEXT, PRIMARY KEY), `release_id` (TEXT), `master_id` (TEXT), `title` (TEXT), `artist` (TEXT), `sides` (TEXT, JSON), `linked` (INTEGER, DEFAULT 0).

#### Scenario: Record table schema
- **WHEN** the database is initialized
- **THEN** the `record` table SHALL exist with columns: id (TEXT PK), release_id (TEXT), master_id (TEXT), title (TEXT), artist (TEXT), sides (TEXT storing JSON), linked (INTEGER DEFAULT 0)

### Requirement: SQLite database has status table
The system SHALL maintain a `status` table with the following column: `updated_at` (TEXT, date).

#### Scenario: Status table schema
- **WHEN** the database is initialized
- **THEN** the `status` table SHALL exist with column: updated_at (TEXT)

### Requirement: Database is created on first access
The system SHALL create the SQLite database file at `data/now-spinning.db` and initialize all tables if the file does not exist.

#### Scenario: Database auto-creation
- **WHEN** the application starts or sync is triggered for the first time
- **THEN** the system SHALL create `data/now-spinning.db` with all required tables if it does not already exist

### Requirement: Database provides last sync date
The system SHALL provide a function to query the last successful sync date from the `status` table.

#### Scenario: No previous sync
- **WHEN** the `status` table has no rows
- **THEN** the function SHALL return `None` (indicating "never")

#### Scenario: Previous sync exists
- **WHEN** the `status` table has a row
- **THEN** the function SHALL return the `updated_at` date value

### Requirement: Record IDs are normalized during extraction
The data extractor SHALL strip leading zeros from record IDs before storing them. The ID "01" SHALL be stored as "1", "001" as "1", etc. Normalization SHALL use integer conversion: `str(int(id_value))`.

#### Scenario: Leading zero in collection.json ID
- **WHEN** a collection.json entry has `"id": "01"`
- **THEN** the extracted record SHALL have `id: "1"`

#### Scenario: ID without leading zero
- **WHEN** a collection.json entry has `"id": "5"`
- **THEN** the extracted record SHALL have `id: "5"`

### Requirement: Manual DB deletion for schema changes
Schema changes are applied by manually deleting the `data/now-spinning.db` file. The `init_db()` function SHALL use `CREATE TABLE IF NOT EXISTS` and SHALL NOT drop tables automatically.

#### Scenario: Database init preserves existing data
- **WHEN** `init_db()` is called and the record table already exists
- **THEN** the existing record table and its data SHALL be preserved

### Requirement: Data extractor resolves album files from release_id
The data extractor SHALL resolve album data files at `data/albums/<release_id>.json` within the repo directory.

#### Scenario: Album file path
- **WHEN** a collection entry has `release_id: "30348842"`
- **THEN** the extractor SHALL look for `data/albums/30348842.json`

### Requirement: Data extractor fails on missing files
The data extractor SHALL raise an error when required files are missing: `styli.json`, `collection.json`, or any album files referenced by the collection.

#### Scenario: Missing album files
- **WHEN** album files are missing for collection entries
- **THEN** the extractor SHALL raise `FileNotFoundError` with the count and first missing path

#### Scenario: Missing collection.json
- **WHEN** `collection.json` does not exist in the repo
- **THEN** the extractor SHALL raise `FileNotFoundError`

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

### Requirement: Database resets stylus hours
The database layer SHALL provide an operation that resets an existing stylus row by setting `distance_hours` to `0`, delegating to the shared absolute-total operation while retaining its boolean updated-row result.

#### Scenario: Reset existing stylus hours
- **WHEN** the reset operation is called for an existing stylus ID
- **THEN** the database SHALL update that stylus row with `distance_hours` equal to `0`
- **AND** the operation SHALL report that a row was updated

#### Scenario: Reset missing stylus hours
- **WHEN** the reset operation is called for a stylus ID that does not exist
- **THEN** the database SHALL leave existing rows unchanged
- **AND** the operation SHALL report that no row was updated

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

### Requirement: Database sets absolute stylus hours
The database layer SHALL provide a shared operation for replacing an existing stylus's `distance_hours` with a finite, nonnegative absolute total. It SHALL use an existing database and a single transaction for reading the previous total and saving the replacement, report the previous and new totals after commit, and report a missing row without creating it. Invalid values or save failures SHALL leave totals unchanged.

#### Scenario: Set replaces rather than increments
- **WHEN** stylus `1` has `102.4` hours and the operation sets `97.3` hours
- **THEN** the committed total SHALL equal `97.3`
- **AND** the operation SHALL report `102.4` as the previous total and `97.3` as the new total

#### Scenario: Reject invalid values
- **WHEN** the operation receives a negative or non-finite value
- **THEN** it SHALL reject the request and leave all saved totals unchanged

#### Scenario: Missing row
- **WHEN** the operation targets a missing stylus
- **THEN** it SHALL report no updated row and leave existing rows unchanged

### Requirement: Collection sync preserves local stylus hours
Collection sync SHALL ignore `distance_hours` from `my-musical-journey` regardless of whether the field remains present. New stylus rows SHALL start at zero hours. Existing rows SHALL retain their local total, including totals previously imported, accrued through playback, or set/reset locally.

#### Scenario: New stylus with legacy remote hours
- **WHEN** sync imports a new stylus whose remote `distance_hours` is `97.3`
- **THEN** its local total SHALL start at zero

#### Scenario: New stylus without remote hours
- **WHEN** sync imports a new stylus without `distance_hours`
- **THEN** its local total SHALL start at zero

#### Scenario: Existing local totals survive sync
- **WHEN** an existing stylus is synced with a different remote total or with the field removed
- **THEN** its local total SHALL remain unchanged

### Requirement: Exactly one locally selected stylus
The database SHALL reuse `stylus.active` to maintain one active stylus whenever styli exist. Legacy normalization SHALL retain the first active ID under the existing ordering, falling back to the first ID if no flag is active, without changing hours or metadata. Activation SHALL verify the target and commit flags in one transaction, leaving flags unchanged for a missing target or failed transaction.

#### Scenario: Legacy flags normalize
- **WHEN** initialization encounters multiple active flags
- **THEN** only the first active ID under the existing ordering SHALL remain active
- **AND** all totals and metadata SHALL be preserved

#### Scenario: No active flag
- **WHEN** initialization encounters nonempty styli without an active flag
- **THEN** the first ID SHALL become active

#### Scenario: Selection survives restart
- **WHEN** activation commits and the application initializes the same database again
- **THEN** the committed selected ID SHALL remain active

### Requirement: Collection sync preserves local selection
Collection sync SHALL preserve the existing local selection and totals regardless of remote active flags and hours. New entries SHALL start at zero hours and SHALL NOT replace an existing selected ID.

#### Scenario: New lower ID arrives
- **WHEN** sync imports a new lower ID with an active remote flag
- **THEN** the previously selected local ID SHALL remain active and its total SHALL remain unchanged

#### Scenario: First sync
- **WHEN** sync imports styli into an empty database
- **THEN** the first ID SHALL become the sole active stylus and all totals SHALL start at zero

### Requirement: Guarded local stylus deletion
Deletion SHALL use an existing database with the active-selection check and deletion in one write transaction. It SHALL raise `ValueError` for the effective active stylus, report a missing ID without creating a row, and report success only after commit. Failure SHALL roll back deletion.

#### Scenario: Inactive deletion
- **WHEN** an inactive stylus is deleted
- **THEN** only that row SHALL be removed and the active selection SHALL be preserved

#### Scenario: Active or failed deletion
- **WHEN** deletion targets the active ID or the write cannot commit
- **THEN** it SHALL fail and all rows SHALL remain unchanged

#### Scenario: Deleted entry returns through sync
- **WHEN** a locally deleted ID is present in a later collection sync
- **THEN** it SHALL be reimported with zero hours without replacing the current selection
