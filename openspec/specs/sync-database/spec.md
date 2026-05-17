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
The system SHALL maintain a `record` table with the following columns: `id` (TEXT, PRIMARY KEY), `release_id` (TEXT), `master_id` (TEXT), `title` (TEXT), `artist` (TEXT), `sides` (TEXT, JSON).

#### Scenario: Record table schema
- **WHEN** the database is initialized
- **THEN** the `record` table SHALL exist with columns: id (TEXT PK), release_id (TEXT), master_id (TEXT), title (TEXT), artist (TEXT), sides (TEXT storing JSON)

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
