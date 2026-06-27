## MODIFIED Requirements

### Requirement: WebSocket endpoint with initial events
The system SHALL provide a WebSocket endpoint that sends initial state events upon connection. The initial temperature event SHALL always represent the current runtime temperature state and SHALL use `temp_c: null` when no real backend temperature reading is available. The server SHALL NOT send a mocked temperature value.

#### Scenario: Client connects before a temperature reading exists
- **WHEN** a client establishes a WebSocket connection before any backend temperature read has succeeded
- **THEN** the server SHALL send `{"event": "temperature_c", "data": {"temp_c": null}}`
- **AND** the server SHALL NOT send a mocked numeric temperature value

#### Scenario: Client connects after a temperature reading exists
- **WHEN** a client establishes a WebSocket connection after the backend has read a temperature of 59.2°C
- **THEN** the server SHALL send `{"event": "temperature_c", "data": {"temp_c": 59.2}}`

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
