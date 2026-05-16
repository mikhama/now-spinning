## ADDED Requirements

### Requirement: WebSocket event broadcast
The WebSocket endpoint SHALL maintain a set of connected clients and support broadcasting events from the POST `/events` endpoint to all connected clients.

#### Scenario: Broadcast to connected client
- **WHEN** a WebSocket client is connected and an event is published via `POST /events`
- **THEN** the client SHALL receive the event as a JSON message

#### Scenario: Multiple connected clients
- **WHEN** two WebSocket clients are connected and an event is published
- **THEN** both clients SHALL receive the event
