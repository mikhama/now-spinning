## ADDED Requirements

### Requirement: Gated kiosk exit endpoint
The system SHALL provide a local `POST /kiosk/exit` endpoint that requests kiosk-mode process shutdown only when kiosk shutdown is explicitly enabled. When kiosk shutdown is not enabled, the endpoint SHALL reject the request without terminating the server process.

#### Scenario: Kiosk exit is enabled
- **WHEN** kiosk shutdown is explicitly enabled
- **AND** a `POST` request is made to `/kiosk/exit`
- **THEN** the server SHALL request termination of the kiosk runner process
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Kiosk exit is disabled
- **WHEN** kiosk shutdown is not explicitly enabled
- **AND** a `POST` request is made to `/kiosk/exit`
- **THEN** the server SHALL reject the request
- **AND** the server process SHALL continue running
