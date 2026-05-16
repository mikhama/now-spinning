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
In boardless mode, events SHALL be publishable from the terminal using a simple HTTP request (e.g., `curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"1"}}' http://localhost:5000/events`).

#### Scenario: Send scan event via curl
- **WHEN** the server is running in boardless mode and the user runs curl to POST a scan event to `/events`
- **THEN** the connected UI client SHALL receive the scan event and transition modes accordingly

#### Scenario: Send status play event via curl
- **WHEN** the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"play"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive the status event and transition to play mode
