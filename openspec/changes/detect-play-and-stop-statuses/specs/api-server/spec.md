## ADDED Requirements

### Requirement: RPM playback status event producer
The API server SHALL run a backend event producer that publishes RPM-derived playback status changes to connected WebSocket clients using the existing status event format.

#### Scenario: Detected playback start broadcasts existing status format
- **WHEN** the RPM playback detector determines that playback has started
- **THEN** the API server SHALL broadcast `{"event": "status", "data": {"status": "play"}}` to connected WebSocket clients
- **AND** the API server SHALL update runtime state as it does for other status events

#### Scenario: Detected playback stop broadcasts existing status format
- **WHEN** the RPM playback detector determines that playback has stopped
- **THEN** the API server SHALL broadcast `{"event": "status", "data": {"status": "stop"}}` to connected WebSocket clients
- **AND** the API server SHALL update runtime state as it does for other status events

#### Scenario: Playback status publisher starts once
- **WHEN** the API server starts playback status publishing more than once in the same process
- **THEN** the API server SHALL create no more than one playback status polling worker

#### Scenario: Missing RPM hardware does not stop API server
- **WHEN** RPM hardware access is unavailable in the runtime environment
- **THEN** the API server SHALL continue serving HTTP and WebSocket requests
- **AND** the playback status event producer SHALL NOT crash the API server process
