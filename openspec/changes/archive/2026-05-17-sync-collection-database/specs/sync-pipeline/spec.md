## ADDED Requirements

### Requirement: Sync pipeline downloads collection from Git
The system SHALL clone the `git@github.com:mikhama/my-musical-journey.git` repository to `tmp/my-musical-journey` when it does not exist locally, or perform a `git pull` if it already exists.

#### Scenario: First sync clones the repository
- **WHEN** the sync pipeline runs and `tmp/my-musical-journey` does not exist
- **THEN** the system SHALL run `git clone git@github.com:mikhama/my-musical-journey.git tmp/my-musical-journey`

#### Scenario: Subsequent sync pulls updates
- **WHEN** the sync pipeline runs and `tmp/my-musical-journey` already exists
- **THEN** the system SHALL run `git pull` inside `tmp/my-musical-journey`

### Requirement: Sync pipeline extracts and upserts data to database
The system SHALL read `data/styli.json`, `data/collection.json`, and all `albums/*.json` files from the cloned repository, upsert the data into the SQLite database, and copy all `images/*.jpeg` files to `ui/images/albums/`.

#### Scenario: Styli data is inserted but not updated
- **WHEN** a stylus from `data/styli.json` has an ID that already exists in the `stylus` table
- **THEN** the system SHALL skip that stylus record without updating it

#### Scenario: Styli data is inserted when new
- **WHEN** a stylus from `data/styli.json` has an ID that does not exist in the `stylus` table
- **THEN** the system SHALL insert the stylus record with all fields: id, name, distance_hours, capacity_min_hours, capacity_max_hours, active

#### Scenario: Record data is inserted when new
- **WHEN** a record from the collection data has an ID that does not exist in the `record` table
- **THEN** the system SHALL insert the record with all fields: id, release_id, master_id, title, artist, sides (as JSON)

#### Scenario: Record data is updated when changed
- **WHEN** a record from the collection data has an ID that already exists in the `record` table and any field has changed
- **THEN** the system SHALL update the existing record with the new data

#### Scenario: Cover images are copied to ui/images/albums
- **WHEN** the sync pipeline processes the cloned repository
- **THEN** the system SHALL copy all `images/*.jpeg` files from the repository to `ui/images/albums/`, overwriting any existing files with the same name

### Requirement: Sync pipeline reports status via SSE
The system SHALL expose a `POST /sync` endpoint that streams Server-Sent Events with status updates for each step of the pipeline.

#### Scenario: Status events sent during sync
- **WHEN** the sync pipeline is running
- **THEN** the endpoint SHALL send SSE events with the following status messages in order:
  1. `Last updated <date>` or `Last updated never`
  2. `Downloading collection`
  3. `Updating database`
  4. `Sync complete` on success or `Sync error` on failure

### Requirement: Sync pipeline updates last sync date
The system SHALL record the current date in the `status` table after a successful sync completes.

#### Scenario: Successful sync updates status
- **WHEN** the sync pipeline completes without errors
- **THEN** the system SHALL update the `updated_at` field in the `status` table to the current date

#### Scenario: Failed sync does not update status
- **WHEN** the sync pipeline encounters an error
- **THEN** the system SHALL NOT update the `updated_at` field in the `status` table

### Requirement: Sync wraps database operations in a transaction
The system SHALL wrap all database inserts and updates within a single transaction per sync run.

#### Scenario: Transaction rollback on error
- **WHEN** an error occurs during database upsert operations
- **THEN** the system SHALL rollback the transaction and report a sync error
