## ADDED Requirements

### Requirement: Offline command deletes inactive styli
The standard-library-only executable SHALL support `./bin/stylus-hours delete <id>`. It SHALL delete only inactive local styli, print success only after commit, and report rejected active deletion, missing database or ID, and write or commit failures to stderr with nonzero status and no success output. It SHALL NOT create a database or schema. List output SHALL identify the active selection.

#### Scenario: Delete inactive entry without site packages
- **WHEN** `delete` runs for an inactive ID with Python site packages disabled
- **THEN** it SHALL remove that row, preserve all other rows, and print success after commit

#### Scenario: Rejected, missing, or failed deletion
- **WHEN** deletion targets the active ID, a missing database or ID, or a database that cannot commit
- **THEN** it SHALL return nonzero with an error on stderr and no success on stdout
- **AND** existing rows SHALL remain unchanged

### Requirement: Deletion instructions require a stopped app
CLI help and README SHALL document selecting another stylus while playback is stopped, exiting normally, waiting for the app to stop, listing IDs, deleting an inactive ID, and restarting. They SHALL explain that deletion is local and collection sync can reimport the ID with zero hours. The completed selection TODO SHALL be removed.

#### Scenario: Operator follows deletion procedure
- **WHEN** an operator reads command help or README deletion instructions
- **THEN** they SHALL find the stopped-app procedure, a deletion example, and the local-only reimport behavior
