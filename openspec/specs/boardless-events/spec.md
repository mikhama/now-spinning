# boardless-events Specification

## Purpose
Event publishing interface for boardless (headless) testing mode, enabling terminal-based event injection via HTTP.
## Requirements
### Requirement: POST events endpoint
The API server SHALL provide a `POST /events` endpoint that accepts a JSON body with `{event, data}` structure and broadcasts the event to all connected WebSocket clients.

#### Scenario: Publish a scan event
- **WHEN** a POST request is made to `/events` with body `{"event": "scan", "data": {"record_id": "1"}}`
- **THEN** the server SHALL broadcast `{"event": "scan", "data": {"record_id": "1"}}` to all connected WebSocket clients and respond with `{"success": true}`

#### Scenario: Publish with no connected clients
- **WHEN** a POST request is made to `/events` with a valid event body and no WebSocket clients are connected
- **THEN** the server SHALL respond with `{"success": true}` without error

#### Scenario: Publish with invalid JSON
- **WHEN** a POST request is made to `/events` with invalid JSON body
- **THEN** the server SHALL respond with 400 status and `{"error": "Invalid JSON"}`

### Requirement: WebSocket client tracking
The server SHALL maintain a set of connected WebSocket clients so the POST events endpoint can broadcast to all of them.

#### Scenario: Client connects and disconnects
- **WHEN** a WebSocket client connects to `/ws`
- **THEN** the server SHALL add it to the connected clients set
- **WHEN** the WebSocket client disconnects
- **THEN** the server SHALL remove it from the connected clients set

### Requirement: Boardless mode event publishing via terminal
In boardless mode, events SHALL be publishable from the terminal using a simple HTTP request (e.g., `curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"1"}}' http://localhost:5000/events`). Boardless Play-mode testing SHALL support a `time` field on `status: "play"` events, formatted as a zero-padded `MM:SS` string, so the connected UI can render the playback time in the Play status bar. A boardless `status: "play"` event with `time` SHALL represent a spinning turntable; any other status SHALL represent a non-spinning turntable.

#### Scenario: Send scan event via curl
- **WHEN** the server is running in boardless mode and the user runs curl to POST a scan event to `/events`
- **THEN** the connected UI client SHALL receive the scan event and transition modes accordingly

#### Scenario: Send status play event via curl with time
- **WHEN** the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"play","time":"00:01"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive the status event
- **AND** the UI SHALL transition to Play mode
- **AND** the Play status bar SHALL render `PLAY 00:01`

#### Scenario: Send status play event represents spinning turntable
- **WHEN** the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"play","time":"03:30"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive the status event
- **AND** the UI SHALL treat the turntable as spinning

#### Scenario: Send status stop event represents stopped turntable
- **WHEN** the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"stop"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive the status event
- **AND** the UI SHALL treat the turntable as not spinning

### Requirement: Boardless link result events
In boardless mode, link workflow results SHALL be publishable from the terminal through `POST /events`. A successful link result SHALL use `{"event":"link_success","data":{"record_id":"<id>"}}`. A failed link result SHALL use `{"event":"link_error","data":{"record_id":"<id>"}}`. The server SHALL broadcast accepted link result events to connected WebSocket clients.

#### Scenario: Send link success event via curl
- **WHEN** the server is running in boardless mode and the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"link_success","data":{"record_id":"1"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive `{"event":"link_success","data":{"record_id":"1"}}`

#### Scenario: Send link error event via curl
- **WHEN** the server is running in boardless mode and the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"link_error","data":{"record_id":"1"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive a `link_error` event with `record_id` "1"

