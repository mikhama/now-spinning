## ADDED Requirements

### Requirement: Flask API server entry point
The system SHALL provide a Flask API server in `api/main.py` that can be run with `python -m api.main`.

#### Scenario: Start the API server
- **WHEN** the user runs `python -m api.main`
- **THEN** the Flask server SHALL start and listen for HTTP and WebSocket connections

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
The system SHALL provide a `GET /records` endpoint that returns all records.

#### Scenario: List all records
- **WHEN** a GET request is made to `/records`
- **THEN** the server SHALL respond with a JSON array of all record objects

### Requirement: GET records by id endpoint
The system SHALL provide a `GET /records/<id>` endpoint that returns a single record.

#### Scenario: Get existing record
- **WHEN** a GET request is made to `/records/1`
- **THEN** the server SHALL respond with the JSON record object with id "1"

#### Scenario: Get non-existing record
- **WHEN** a GET request is made to `/records/<id>` where id does not exist
- **THEN** the server SHALL respond with 404 status

### Requirement: POST records link endpoint
The system SHALL provide a `POST /records/<id>/link` endpoint.

#### Scenario: Link a record
- **WHEN** a POST request is made to `/records/1/link`
- **THEN** the server SHALL respond with `{ "success": true }`

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
The system SHALL provide a `POST /styli/<id>/reset` endpoint.

#### Scenario: Reset stylus hours
- **WHEN** a POST request is made to `/styli/1/reset`
- **THEN** the server SHALL respond with `{ "success": true }`

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
