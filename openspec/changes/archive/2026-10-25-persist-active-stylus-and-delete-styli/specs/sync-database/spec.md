## ADDED Requirements

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
