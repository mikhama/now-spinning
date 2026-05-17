## MODIFIED Requirements

### Requirement: SQLite database has record table
The system SHALL maintain a `record` table with the following columns: `id` (TEXT, PRIMARY KEY), `release_id` (TEXT), `master_id` (TEXT), `title` (TEXT), `artist` (TEXT), `sides` (TEXT, JSON), `linked` (INTEGER, DEFAULT 0).

#### Scenario: Record table schema
- **WHEN** the database is initialized
- **THEN** the `record` table SHALL exist with columns: id (TEXT PK), release_id (TEXT), master_id (TEXT), title (TEXT), artist (TEXT), sides (TEXT storing JSON), linked (INTEGER DEFAULT 0)

## ADDED Requirements

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
