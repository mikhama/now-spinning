## ADDED Requirements

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

## MODIFIED Requirements

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
