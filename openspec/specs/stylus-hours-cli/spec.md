# stylus-hours-cli Specification

## Purpose
Provide offline commands for inspecting and managing locally saved stylus usage totals.

## Requirements

### Requirement: Offline command lists saved stylus totals
The executable `./bin/stylus-hours list` SHALL display the ID, name, and saved hours of every stylus in the existing project database at `data/now-spinning.db`, using Python's built-in SQLite support without requiring a running application or its third-party dependencies.

#### Scenario: List saved styli
- **WHEN** the existing database contains multiple styli
- **THEN** `list` SHALL display each ID, name, and saved total
- **AND** it SHALL leave the saved totals unchanged and return success

#### Scenario: Empty stylus table
- **WHEN** the existing database has no styli
- **THEN** `list` SHALL indicate that there are no styli and return success

### Requirement: Offline command sets or resets an absolute total
The command `./bin/stylus-hours set <id> <hours>` SHALL replace the existing stylus's total with the specified finite, nonnegative hours, without adding to it or rounding it. `./bin/stylus-hours reset <id>` SHALL perform the same operation with zero. A successful change SHALL display the previous and new totals and return success only after commit.

#### Scenario: Replace saved hours
- **WHEN** stylus `1` has `102.4` hours and the operator runs `set 1 97.3`
- **THEN** a new connection SHALL read the stored total as `97.3`
- **AND** the command SHALL display `Stylus 1: 102.4 hours -> 97.3 hours`

#### Scenario: Reset saved hours
- **WHEN** the operator runs `reset 1` for an existing stylus
- **THEN** that stylus's saved total SHALL become zero
- **AND** the command SHALL display its previous and new totals

#### Scenario: Preserve precision and other styli
- **WHEN** the operator sets one stylus to a valid total with more than one fractional digit
- **THEN** the saved total SHALL equal the specified value in SQLite REAL precision
- **AND** other styli and the stylus's metadata SHALL remain unchanged

### Requirement: Offline command fails safely
The command SHALL report errors to stderr and return a failure status for a missing database, missing stylus, invalid hours, invalid command arguments, or a failed save. It SHALL NOT create a missing database or initialize a schema. A rejected or failed change SHALL leave stored totals unchanged and SHALL NOT report a successful change.

#### Scenario: Invalid hours
- **WHEN** `set` receives negative, nonnumeric, NaN, infinite, or overflow-to-infinity hours
- **THEN** it SHALL fail and leave the stored total unchanged

#### Scenario: Missing database
- **WHEN** any command runs without the existing project database
- **THEN** it SHALL fail with an error and SHALL NOT create the database

#### Scenario: Missing stylus
- **WHEN** `set` or `reset` targets a missing ID
- **THEN** it SHALL fail and leave all existing rows unchanged

#### Scenario: Save failure
- **WHEN** the database cannot commit an update
- **THEN** the command SHALL fail without reporting success
- **AND** the transaction SHALL roll back

### Requirement: Offline operation requires a stopped app
The command SHALL have no application lock. Command help and usage instructions SHALL require the operator to exit the app normally, wait until it stops, list styli, set/reset an ID, and restart the app. Instructions SHALL explain the pending-usage risk and require syncing a new Pi's collection before stopping the app and setting initial hours.

#### Scenario: Restart uses saved hours
- **WHEN** the operator stops the app, sets or resets a total, and restarts the app
- **THEN** the app SHALL load that saved total for display and subsequent playback tracking

#### Scenario: New Pi setup
- **WHEN** an operator follows the instructions on a new Pi
- **THEN** the instructions SHALL direct them to sync the collection first and then stop the app before setting initial local hours

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
