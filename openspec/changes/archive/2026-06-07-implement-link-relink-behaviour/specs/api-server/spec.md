## MODIFIED Requirements

### Requirement: POST records link endpoint
The system SHALL provide a `POST /records/<id>/link` endpoint that marks the matching database record as linked. When the record exists, the server SHALL persist `linked = true` and respond with `{ "success": true }`. When the record does not exist, the server SHALL respond with 404.

#### Scenario: Link a record
- **WHEN** a POST request is made to `/records/1/link` and record "1" exists
- **THEN** the server SHALL persist record "1" with `linked: true`
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Link a missing record
- **WHEN** a POST request is made to `/records/999/link` and record "999" does not exist
- **THEN** the server SHALL respond with 404 status

## ADDED Requirements

### Requirement: POST events persists link success
When `POST /events` receives a `link_success` event with a `record_id`, the server SHALL mark that database record as linked before broadcasting the event. If the record does not exist or the payload is missing `record_id`, the server SHALL return an error response and SHALL NOT broadcast `link_success`.

#### Scenario: Link success event persists linked state
- **WHEN** a POST request is made to `/events` with `{"event":"link_success","data":{"record_id":"1"}}` and record "1" exists
- **THEN** the server SHALL persist record "1" with `linked: true`
- **AND** the server SHALL broadcast the `link_success` event to connected WebSocket clients
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Link success missing record_id
- **WHEN** a POST request is made to `/events` with `{"event":"link_success","data":{}}`
- **THEN** the server SHALL respond with 400 status
- **AND** the server SHALL NOT broadcast `link_success`

#### Scenario: Link success for unknown record
- **WHEN** a POST request is made to `/events` with `{"event":"link_success","data":{"record_id":"999"}}` and record "999" does not exist
- **THEN** the server SHALL respond with 404 status
- **AND** the server SHALL NOT broadcast `link_success`
