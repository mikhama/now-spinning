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

