## MODIFIED Requirements

### Requirement: GET records endpoint reads from database
The system SHALL provide a `GET /records` endpoint that reads records from the SQLite database (not mock data), including the `linked` field (boolean) and a derived `cover_image` path for each record.

#### Scenario: List all records with linked status
- **WHEN** a GET request is made to `/records`
- **THEN** the server SHALL respond with a JSON array of all record objects from the database, each including `linked: true` or `linked: false` and `cover_image` derived as `images/albums/<release_id>.jpeg`

### Requirement: Sync endpoint reports errors cleanly
The sync endpoint SHALL log full error details (with traceback) to backend logs and send a clean "Sync error" message to the frontend SSE stream without exposing internal paths or details.

#### Scenario: Sync fails due to missing files
- **WHEN** the sync pipeline raises an error
- **THEN** the SSE stream SHALL send `{"status": "Sync error"}` and the backend log SHALL contain the full exception with traceback
