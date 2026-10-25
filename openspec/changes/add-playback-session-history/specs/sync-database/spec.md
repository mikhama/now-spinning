## MODIFIED Requirements

### Requirement: Manual DB deletion for schema changes
Additive schema changes SHALL be applied during normal database initialization without requiring manual deletion of `data/now-spinning.db`. The `init_db()` function SHALL use `CREATE TABLE IF NOT EXISTS` and SHALL NOT drop tables automatically.

#### Scenario: Database init preserves existing data
- **WHEN** `init_db()` is called and the record table already exists
- **THEN** the existing record table and its data SHALL be preserved
- **AND** existing stylus totals and playback history SHALL be preserved

## ADDED Requirements

### Requirement: Additive playback history storage
Normal database initialization SHALL add `sessions_log` with an integer primary key `id`, nonempty local `record_id`, `session_started_at` text, and positive integer `session_duration_sec`, preserving existing records and stylus totals. Writers SHALL store UTC ISO 8601 timestamps with an explicit offset. History SHALL survive initialization and collection sync, including later loss of record metadata.

#### Scenario: Upgrade existing database
- **WHEN** initialization runs against a database containing records and stylus totals
- **THEN** it SHALL create the history table without changing those records or totals
- **AND** repeated initialization and collection sync SHALL preserve committed history

#### Scenario: Invalid duration
- **WHEN** a history write supplies zero, negative, or fractional seconds
- **THEN** the database SHALL reject the write

### Requirement: Atomic history persistence and deletion
History batch writes and history clearing SHALL each commit in one transaction and report success only after commit. A failed transaction SHALL leave saved history unchanged. Neither console operation SHALL create a database or upgrade its schema.

#### Scenario: Commit fails
- **WHEN** a history insert batch or clear cannot commit
- **THEN** all changes in that transaction SHALL roll back
- **AND** the operation SHALL report failure
