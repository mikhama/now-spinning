## MODIFIED Requirements

### Requirement: Boardless mode event publishing via terminal
In boardless mode, events SHALL be publishable from the terminal using a simple HTTP request (e.g., `curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"1"}}' http://localhost:5000/events`). Boardless Play-mode testing SHALL support a `time` field on `status: "play"` events, formatted as a zero-padded `MM:SS` string, so the connected UI can render the playback time in the Play status bar.

#### Scenario: Send scan event via curl
- **WHEN** the server is running in boardless mode and the user runs curl to POST a scan event to `/events`
- **THEN** the connected UI client SHALL receive the scan event and transition modes accordingly

#### Scenario: Send status play event via curl with time
- **WHEN** the user runs `curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"play","time":"00:01"}}' http://localhost:5000/events`
- **THEN** the connected UI client SHALL receive the status event
- **AND** the UI SHALL transition to Play mode
- **AND** the Play status bar SHALL render `PLAY 00:01`