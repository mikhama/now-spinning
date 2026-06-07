# api-server Specification

## Purpose
TBD - created by archiving change api-mocked-server. Update Purpose after archive.
## Requirements
### Requirement: Flask API server entry point
The system SHALL provide a Flask API server in `api/main.py` that can be run with `python -m api.main`. The Flask app SHALL serve the `ui/` directory as static files at the root URL path, making `index.html`, `style.css`, `app.js`, and `images/` accessible to the browser.

#### Scenario: Start the API server
- **WHEN** the user runs `python -m api.main`
- **THEN** the Flask server SHALL start and listen for HTTP and WebSocket connections

#### Scenario: Serve the frontend HTML page
- **WHEN** a GET request is made to `/`
- **THEN** the server SHALL respond with the contents of `ui/index.html`

#### Scenario: Serve static CSS file
- **WHEN** a GET request is made to `/style.css`
- **THEN** the server SHALL respond with the contents of `ui/style.css`

#### Scenario: Serve static JS file
- **WHEN** a GET request is made to `/app.js`
- **THEN** the server SHALL respond with the contents of `ui/app.js`

#### Scenario: Serve cover image assets
- **WHEN** a GET request is made to `/images/30348842.jpeg`
- **THEN** the server SHALL respond with the image file from `ui/images/`

### Requirement: Pydantic data models
The system SHALL define Pydantic models in `api/models.py`.

#### Scenario: Record model structure
- **WHEN** a Record model is instantiated
- **THEN** it SHALL have fields: `id` (str), `release_id` (str), `master_id` (str), `title` (str), `artist` (str), `cover_image` (str), `linked` (bool), and `sides` (list of Side)

#### Scenario: Side model structure
- **WHEN** a Side model is instantiated
- **THEN** it SHALL have fields: `id` (str) and `tracks` (list of Track)

#### Scenario: Track model structure
- **WHEN** a Track model is instantiated
- **THEN** it SHALL have fields: `title` (str), `artist` (str | None), `duration` (str in MM:SS format like \"03:29\")

#### Scenario: Stylus model structure
- **WHEN** a Stylus model is instantiated
- **THEN** it SHALL have fields: `id` (str), `name` (str), `hours` (float)

### Requirement: GET records endpoint
The system SHALL provide a `GET /records` endpoint that reads records from the SQLite database (not mock data), including the `linked` field (boolean) and a derived `cover_image` path for each record.

#### Scenario: List all records with linked status
- **WHEN** a GET request is made to `/records`
- **THEN** the server SHALL respond with a JSON array of all record objects from the database, each including `linked: true` or `linked: false` and `cover_image` derived as `images/albums/<release_id>.jpeg`

### Requirement: GET records by id endpoint
The system SHALL provide a `GET /records/<id>` endpoint that returns a single record.

#### Scenario: Get existing record
- **WHEN** a GET request is made to `/records/1`
- **THEN** the server SHALL respond with the JSON record object with id "1"

#### Scenario: Get non-existing record
- **WHEN** a GET request is made to `/records/<id>` where id does not exist
- **THEN** the server SHALL respond with 404 status

### Requirement: POST records link endpoint
The system SHALL provide a `POST /records/<id>/link` endpoint that marks the matching database record as linked. When the record exists, the server SHALL persist `linked = true` and respond with `{ "success": true }`. When the record does not exist, the server SHALL respond with 404.

#### Scenario: Link a record
- **WHEN** a POST request is made to `/records/1/link` and record "1" exists
- **THEN** the server SHALL persist record "1" with `linked: true`
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Link a missing record
- **WHEN** a POST request is made to `/records/999/link` and record "999" does not exist
- **THEN** the server SHALL respond with 404 status

### Requirement: POST records sync endpoint
The system SHALL provide a `POST /records/sync` endpoint.

#### Scenario: Sync records
- **WHEN** a POST request is made to `/records/sync`
- **THEN** the server SHALL respond with `{ "success": true }`

### Requirement: GET styli endpoint
The system SHALL provide a `GET /styli` endpoint that returns all styli.

#### Scenario: List all styli
- **WHEN** a GET request is made to `/styli`
- **THEN** the server SHALL respond with a JSON array of all stylus objects

### Requirement: GET styli by id endpoint
The system SHALL provide a `GET /styli/<id>` endpoint that returns a single stylus.

#### Scenario: Get existing stylus
- **WHEN** a GET request is made to `/styli/1`
- **THEN** the server SHALL respond with the JSON stylus object with id "1"

#### Scenario: Get non-existing stylus
- **WHEN** a GET request is made to `/styli/<id>` where id does not exist
- **THEN** the server SHALL respond with 404 status

### Requirement: POST styli reset endpoint
The system SHALL provide a `POST /styli/<id>/reset` endpoint that resets the matching stylus hours in persistent storage. When the stylus exists, the server SHALL persist `distance_hours = 0` for that stylus and respond with `{ "success": true }`. When the stylus does not exist, the server SHALL respond with 404.

#### Scenario: Reset stylus hours
- **WHEN** a POST request is made to `/styli/1/reset` and stylus "1" exists
- **THEN** the server SHALL persist stylus "1" with `distance_hours` equal to `0`
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Reset missing stylus
- **WHEN** a POST request is made to `/styli/999/reset` and stylus "999" does not exist
- **THEN** the server SHALL respond with 404 status

### Requirement: POST styli sync endpoint
The system SHALL provide a `POST /styli/sync` endpoint.

#### Scenario: Sync styli
- **WHEN** a POST request is made to `/styli/sync`
- **THEN** the server SHALL respond with `{ "success": true }`

### Requirement: POST shutdown endpoint
The system SHALL provide a `POST /shutdown` endpoint.

#### Scenario: Shutdown server
- **WHEN** a POST request is made to `/shutdown`
- **THEN** the server SHALL respond with `{ "success": true }`

### Requirement: WebSocket endpoint with initial events
The system SHALL provide a WebSocket endpoint that sends initial state events upon connection.

#### Scenario: Client connects to WebSocket
- **WHEN** a client establishes a WebSocket connection
- **THEN** the server SHALL send four JSON events in sequence:
  1. `{"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}}`
  2. `{"event": "temperature_c", "data": {"temp_c": 59}}`
  3. `{"event": "current_record", "data": {"record_id": "1"}}`
  4. `{"event": "status", "data": {"status": "idle"}}`

### Requirement: Mock record data
The system SHALL include mock data for one record: Linkin Park — Papercuts (Discogs release 30348842, master 3453923) with id "1".

#### Scenario: Papercuts record data
- **WHEN** the mock record with id "1" is retrieved
- **THEN** it SHALL contain: title "Papercuts", artist "Linkin Park", release_id "30348842", master_id "3453923", cover_image path, linked false, and 4 sides (A, B, C, D) each with 5 tracks with correct titles and durations

### Requirement: Mock stylus data
The system SHALL include mock data for one stylus with id "1".

#### Scenario: Sumiko Olympia stylus data
- **WHEN** the mock stylus with id "1" is retrieved
- **THEN** it SHALL contain: name "Sumiko Olympia", hours 89.6

### Requirement: Cover image asset
The system SHALL store the Papercuts album cover image at `ui/images/30348842.jpeg`.

#### Scenario: Cover image exists
- **WHEN** the application is set up
- **THEN** the file `ui/images/30348842.jpeg` SHALL exist and contain the album cover art from Discogs release 30348842

### Requirement: WebSocket event broadcast
The WebSocket endpoint SHALL maintain a set of connected clients and support broadcasting events from the POST `/events` endpoint to all connected clients.

#### Scenario: Broadcast to connected client
- **WHEN** a WebSocket client is connected and an event is published via `POST /events`
- **THEN** the client SHALL receive the event as a JSON message

#### Scenario: Multiple connected clients
- **WHEN** two WebSocket clients are connected and an event is published
- **THEN** both clients SHALL receive the event

### Requirement: Sync endpoint reports errors cleanly
The sync endpoint SHALL log full error details (with traceback) to backend logs and send a clean "Sync error" message to the frontend SSE stream without exposing internal paths or details.

#### Scenario: Sync fails due to missing files
- **WHEN** the sync pipeline raises an error
- **THEN** the SSE stream SHALL send `{"status": "Sync error"}` and the backend log SHALL contain the full exception with traceback

### Requirement: POST events persists link success
When `POST /events` receives a `link_success` event with a `record_id`, the server SHALL mark that database record as linked before broadcasting the event. If the record does not exist or the payload is missing `record_id`, the server SHALL return an error response and SHALL NOT broadcast `link_success`.

#### Scenario: Link success event persists linked state
- **WHEN** a POST request is made to `/events` with `{"event":"link_success","data":{"record_id":"1"}}` and record "1" exists
- **THEN** the server SHALL persist record "1" with `linked: true`
- **AND** the server SHALL broadcast the `link_success` event to connected WebSocket clients
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Link success missing record_id
- **WHEN** a POST request is made to `/events` with `{"event":"link_success","data":{}}`
- **THEN** the server SHALL respond with 400 status
- **AND** the server SHALL NOT broadcast `link_success`

#### Scenario: Link success for unknown record
- **WHEN** a POST request is made to `/events` with `{"event":"link_success","data":{"record_id":"999"}}` and record "999" does not exist
- **THEN** the server SHALL respond with 404 status
- **AND** the server SHALL NOT broadcast `link_success`
