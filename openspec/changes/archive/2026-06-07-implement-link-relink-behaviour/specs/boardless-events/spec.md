## ADDED Requirements

### Requirement: Boardless link result events
In boardless mode, link workflow results SHALL be publishable from the terminal through `POST /events`. A successful link result SHALL use `{"event":"link_success","data":{"record_id":"<id>"}}`. A failed link result SHALL use `{"event":"link_error","data":{"record_id":"<id>"}}`. The server SHALL broadcast accepted link result events to connected WebSocket clients.

#### Scenario: Send link success event via curl
- **WHEN** the server is running in boardless mode and the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"link_success","data":{"record_id":"1"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive `{"event":"link_success","data":{"record_id":"1"}}`

#### Scenario: Send link error event via curl
- **WHEN** the server is running in boardless mode and the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"link_error","data":{"record_id":"1"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive a `link_error` event with `record_id` "1"
