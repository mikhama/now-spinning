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
The system SHALL implement `POST /shutdown` as orderly system poweroff only for loopback peer requests on Linux when `KIOSK_SHUTDOWN_ENABLED=true` and boardless mode is disabled. It SHALL persist pending stylus usage first, abort on persistence failure, and then invoke the fixed subprocess argument list `sudo -n /usr/bin/systemctl poweroff` with a bounded five-second timeout and no shell. Accepted actions SHALL return `{ "success": true }`; disabled actions SHALL return a JSON error with HTTP 403, and persistence or execution failures SHALL return a JSON error with HTTP 500.

#### Scenario: Accepted shutdown
- **WHEN** all shutdown gates pass and pending stylus usage is persisted successfully
- **THEN** the fixed poweroff command SHALL run after persistence and return JSON success on a zero exit status

#### Scenario: Disabled shutdown
- **WHEN** the peer is not loopback, the platform is not Linux, shutdown is disabled, or boardless mode is enabled
- **THEN** the endpoint SHALL return JSON 403 without flushing usage or invoking poweroff
- **AND** forwarding headers SHALL NOT bypass the loopback peer check

#### Scenario: Persistence fails
- **WHEN** the pending stylus usage cannot be persisted, including an unsuccessful database update
- **THEN** the endpoint SHALL return JSON 500 and SHALL NOT invoke poweroff

#### Scenario: Poweroff execution fails
- **WHEN** sudo or systemctl fails, cannot be executed, or exceeds the bounded timeout
- **THEN** the endpoint SHALL return JSON 500 without reporting acceptance

### Requirement: Gated kiosk exit endpoint
The system SHALL provide `POST /kiosk/exit` to request kiosk-runner termination only when kiosk shutdown is explicitly enabled and boardless mode is disabled. Rejected requests SHALL return JSON 403 without terminating the server process. Accepted requests SHALL preserve `{ "success": true }` and the runner cleanup that terminates Chromium and the API. Failure to persist usage or schedule termination SHALL return a JSON error with HTTP 500.

#### Scenario: Kiosk exit is enabled
- **WHEN** kiosk shutdown is enabled and boardless mode is disabled
- **AND** a `POST` request is made to `/kiosk/exit`
- **THEN** the server SHALL flush pending stylus hours before scheduling kiosk runner termination and return JSON success

#### Scenario: Kiosk exit is disabled
- **WHEN** kiosk shutdown is disabled or boardless mode is enabled
- **AND** a `POST` request is made to `/kiosk/exit`
- **THEN** the server SHALL return JSON 403 without flushing or terminating

#### Scenario: Kiosk exit fails
- **WHEN** persistence or scheduling termination fails
- **THEN** the server SHALL return JSON 500 without reporting acceptance

### Requirement: WebSocket endpoint with initial events
The system SHALL provide a WebSocket endpoint that sends initial state events upon connection. The initial temperature event SHALL always represent the current runtime temperature state and SHALL use `temp_c: null` when no real backend temperature reading is available. The server SHALL NOT send a mocked temperature value. An externally supplied null scan that occurs after a successful non-null scan or established current record SHALL NOT replace the last resolved record event in the runtime snapshot sent to newly connected clients. A null scan error before any such success SHALL be available as the startup NFC error snapshot.

#### Scenario: Client connects before a temperature reading exists
- **WHEN** a client establishes a WebSocket connection before any backend temperature read has succeeded
- **THEN** the server SHALL send `{"event": "temperature_c", "data": {"temp_c": null}}`
- **AND** the server SHALL NOT send a mocked numeric temperature value

#### Scenario: Client connects after a temperature reading exists
- **WHEN** a client establishes a WebSocket connection after the backend has read a temperature of 59.2°C
- **THEN** the server SHALL send `{"event": "temperature_c", "data": {"temp_c": 59.2}}`

#### Scenario: Client connects after a startup NFC error
- **WHEN** a null scan error occurred before any successful non-null scan or current record
- **AND** a client establishes a WebSocket connection
- **THEN** the server SHALL seed the client with `{"event":"scan","data":{"record_id":null}}`

#### Scenario: Client reconnects after a successful scan and later external null event
- **WHEN** a non-null scan for record id `1` was broadcast and a later external null scan was broadcast
- **AND** a client establishes a WebSocket connection
- **THEN** the server SHALL seed the client with `{"event":"scan","data":{"record_id":"1"}}`
- **AND** the server SHALL NOT seed the client with the later null scan

#### Scenario: Client reconnects after an established current record and later external null event
- **WHEN** a `current_record` event established record id `1` and a later external null scan was broadcast
- **AND** a client establishes a WebSocket connection
- **THEN** the server SHALL seed the client with `{"event":"current_record","data":{"record_id":"1"}}`
- **AND** the server SHALL NOT seed the client with the later null scan

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
The WebSocket endpoint SHALL maintain a set of connected clients and support broadcasting events from backend event producers and the POST `/events` endpoint to all connected clients.

#### Scenario: Broadcast to connected client
- **WHEN** a WebSocket client is connected and an event is published via `POST /events`
- **THEN** the client SHALL receive the event as a JSON message

#### Scenario: Backend temperature broadcast
- **WHEN** the backend temperature publisher emits a `temperature_c` event
- **THEN** each connected WebSocket client SHALL receive the event as a JSON message

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

### Requirement: Hardware sensor startup readiness
The API server SHALL verify required hardware sensor readiness at the beginning of hardware-mode startup before starting background event producers or accepting HTTP and WebSocket connections. Required hardware sensors SHALL include the NFC sensor and RPM playback sensor. When `BOARDLESS_MODE=true`, the API server SHALL NOT require physical hardware sensor readiness.

#### Scenario: Hardware sensors are ready before server starts
- **WHEN** the API server starts with boardless mode disabled
- **AND** the NFC sensor initializes successfully
- **AND** the RPM playback sensor initializes successfully and returns an initial RPM sample
- **THEN** startup SHALL continue to background event producer startup
- **AND** the Flask server SHALL be allowed to start

#### Scenario: NFC sensor is not ready during hardware startup
- **WHEN** the API server starts with boardless mode disabled
- **AND** the NFC sensor cannot initialize successfully
- **THEN** startup SHALL raise an error immediately
- **AND** the API server SHALL NOT start background event producers
- **AND** the API server SHALL NOT accept HTTP or WebSocket connections

#### Scenario: RPM playback sensor is not ready during hardware startup
- **WHEN** the API server starts with boardless mode disabled
- **AND** the RPM playback sensor cannot initialize successfully or cannot return an initial RPM sample
- **THEN** startup SHALL raise an error immediately
- **AND** the API server SHALL NOT start background event producers
- **AND** the API server SHALL NOT accept HTTP or WebSocket connections

#### Scenario: Boardless startup does not require physical sensors
- **WHEN** the API server starts with `BOARDLESS_MODE=true`
- **THEN** startup SHALL NOT require NFC or RPM playback hardware readiness
- **AND** the Flask server SHALL be allowed to start

### Requirement: RPM playback status event producer
The API server SHALL run a backend event producer that publishes RPM-derived playback status changes to connected WebSocket clients using the existing status event format. In hardware mode, RPM reader readiness SHALL be verified before the API server starts accepting requests.

#### Scenario: Detected playback start broadcasts existing status format with time
- **WHEN** the RPM playback detector determines that playback has started
- **THEN** the API server SHALL broadcast `{"event": "status", "data": {"status": "play", "time": "00:00"}}` to connected WebSocket clients
- **AND** later playback time updates SHALL use the same event shape with `time` formatted as zero-padded `MM:SS`
- **AND** the API server SHALL update runtime state as it does for other status events

#### Scenario: Detected playback stop broadcasts existing status format
- **WHEN** the RPM playback detector determines that playback has stopped
- **THEN** the API server SHALL broadcast `{"event": "status", "data": {"status": "stop"}}` to connected WebSocket clients
- **AND** the API server SHALL update runtime state as it does for other status events

#### Scenario: Playback status publisher starts once
- **WHEN** the API server starts playback status publishing more than once in the same process
- **THEN** the API server SHALL create no more than one playback status polling worker

#### Scenario: Missing RPM hardware fails hardware-mode startup
- **WHEN** RPM hardware access is unavailable during startup
- **AND** boardless mode is disabled
- **THEN** the API server SHALL raise a startup error
- **AND** the API server SHALL NOT start accepting HTTP or WebSocket requests

#### Scenario: Missing RPM hardware is allowed in boardless mode
- **WHEN** RPM hardware access is unavailable during startup
- **AND** `BOARDLESS_MODE=true`
- **THEN** the API server SHALL continue startup without requiring the RPM hardware sensor

### Requirement: Kiosk exit flushes stylus hours
When kiosk shutdown is enabled and the API server accepts a `POST /kiosk/exit` request, the server SHALL flush pending stylus-hour usage before requesting kiosk runner termination.

#### Scenario: Enabled kiosk exit flushes pending stylus hours
- **WHEN** kiosk shutdown is explicitly enabled
- **AND** an active stylus has pending unflushed playback usage
- **AND** a `POST` request is made to `/kiosk/exit`
- **THEN** the API server SHALL persist the pending stylus-hour usage
- **AND** the API server SHALL request termination of the kiosk runner process
- **AND** the API server SHALL respond with `{ "success": true }`

#### Scenario: Disabled kiosk exit does not flush or terminate
- **WHEN** kiosk shutdown is not explicitly enabled
- **AND** an active stylus has pending unflushed playback usage
- **AND** a `POST` request is made to `/kiosk/exit`
- **THEN** the API server SHALL reject the request
- **AND** the API server SHALL NOT request termination of the kiosk runner process

### Requirement: Server shutdown hooks flush stylus hours
The API server SHALL attempt to flush pending stylus-hour usage when the process receives a normal shutdown signal or runs registered process-exit cleanup.

#### Scenario: Shutdown cleanup flushes pending stylus usage
- **WHEN** an active stylus has pending unflushed playback usage
- **AND** the API server runs normal shutdown cleanup
- **THEN** the API server SHALL attempt to persist the pending stylus-hour usage before process exit

### Requirement: NFC worker shutdown is terminal and owns cleanup
When shutdown starts, the NFC worker SHALL reject new operations, discard queued work, and let its active operation finish. The polling pause SHALL be interruptible. The worker SHALL close the reader in its `finally` block and record cleanup success or failure. Mode changes SHALL NOT restart work after shutdown starts. Hardware commands SHALL remain in the worker, including reader close.

#### Scenario: Stop during idle polling
- **WHEN** shutdown starts during a polling pause
- **THEN** the worker SHALL wake, close the reader, and exit

#### Scenario: Stop during a read
- **WHEN** shutdown starts during a Standby read with a queued write
- **THEN** the active read SHALL finish before reader close and the queued write SHALL NOT start
- **AND** a failed read SHALL preserve the last successful record

#### Scenario: Stop during a confirmed write
- **WHEN** an active write succeeds within the shutdown wait
- **THEN** the worker SHALL keep its existing persistence and completion event behavior before reader close

### Requirement: Application cleanup has one bounded NFC wait
The application SHALL retain its NFC thread reference and use one cleanup path for termination signals, normal server exit, startup failure, and process-exit cleanup. It SHALL request worker shutdown and wait up to five seconds, including reader close. If the worker remains active, it SHALL log incomplete cleanup and continue exit without a competing reader command. Repeated cleanup calls and signals SHALL be safe. If startup fails before the worker starts, cleanup SHALL close an initialized reader without initializing another reader. Stylus persistence checks and the existing Exit response SHALL remain in effect.

#### Scenario: Terminate during a Standby read
- **WHEN** the application receives SIGTERM during a Standby read that finishes within five seconds
- **THEN** reader cleanup SHALL complete before normal process exit

#### Scenario: Worker stays blocked
- **WHEN** an active read, write, or reader close remains blocked for five seconds
- **THEN** application cleanup SHALL report incomplete cleanup and return without another hardware command

#### Scenario: Startup fails after reader initialization
- **WHEN** a later startup check fails before the worker starts
- **THEN** cleanup SHALL close the existing reader and preserve the startup failure

#### Scenario: Cleanup paths repeat
- **WHEN** signals, server cleanup, or process-exit cleanup run more than once
- **THEN** they SHALL NOT repeat reader close or extend the NFC shutdown wait

### Requirement: NFC requests report shutdown
New NFC mode and write requests during shutdown SHALL return JSON with HTTP status 503. The coordinator SHALL also reject requests that race with shutdown.

#### Scenario: Request arrives after stop
- **WHEN** `/nfc/mode` or `/nfc/write` receives a request after shutdown starts
- **THEN** it SHALL return JSON 503 and SHALL NOT queue work

### Requirement: NFC lifecycle logs distinguish operation and cleanup failures
The application SHALL log NFC mode transitions, operation outcomes, and shutdown results. Failure logs SHALL include the exception chain. Local validation and Pi validation SHALL be reported separately. A hardware fix SHALL be confirmed only after the user verifies the application on the Pi after deployment. The reported sequences are Scan → play → stop → Standby → Exit → reopen and scan 1 → 43 → 15 → 23 → 1 → Exit → reopen.

#### Scenario: Read fails before shutdown
- **WHEN** a read fails and the application later exits
- **THEN** logs SHALL identify the read failure separately from the reader cleanup result

#### Scenario: Hardware validation remains pending
- **WHEN** only local tests have passed
- **THEN** the verification record SHALL state that the Pi restart fault is not yet verified as fixed

### Requirement: Stylus responses expose saved selection
Stylus list and individual responses, including model and mock data, SHALL include a boolean `active`. Lists SHALL use stable text-ID order.

#### Scenario: List and detail agree
- **WHEN** clients request styli and an individual saved stylus
- **THEN** their boolean active flags SHALL agree with persisted selection

### Requirement: Guarded stylus activation endpoint
The server SHALL provide `POST /styli/<id>/activate`, returning JSON `{"success": true}` only after persistence, JSON 404 for a missing target, JSON 500 on persistence failure, and JSON 409 when backend playback status is `play`. The playback guard and persistence SHALL be serialized with playback transitions under the tracker's lock regardless of UI mode, debug hash, or request source.

#### Scenario: Stopped activation
- **WHEN** an existing stylus is activated while backend playback is stopped
- **THEN** the selected ID SHALL persist before success is returned

#### Scenario: Playback rejection
- **WHEN** activation is requested during backend playback
- **THEN** the server SHALL return JSON 409 without changing selection, hours, pending usage, or tracking baseline

#### Scenario: Playback start races activation
- **WHEN** activation races a playback-start transition
- **THEN** either activation SHALL commit before playback starts or activation SHALL return 409
- **AND** playback SHALL NOT start between the guard and persistence

#### Scenario: Missing or failed persistence
- **WHEN** the target is missing or persistence fails while stopped
- **THEN** the server SHALL return JSON 404 or 500 respectively without selecting a different stylus
