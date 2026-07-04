## ADDED Requirements

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
