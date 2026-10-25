## MODIFIED Requirements

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
