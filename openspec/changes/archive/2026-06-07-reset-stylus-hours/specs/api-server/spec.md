## MODIFIED Requirements

### Requirement: POST styli reset endpoint
The system SHALL provide a `POST /styli/<id>/reset` endpoint that resets the matching stylus hours in persistent storage. When the stylus exists, the server SHALL persist `distance_hours = 0` for that stylus and respond with `{ "success": true }`. When the stylus does not exist, the server SHALL respond with 404.

#### Scenario: Reset stylus hours
- **WHEN** a POST request is made to `/styli/1/reset` and stylus "1" exists
- **THEN** the server SHALL persist stylus "1" with `distance_hours` equal to `0`
- **AND** the server SHALL respond with `{ "success": true }`

#### Scenario: Reset missing stylus
- **WHEN** a POST request is made to `/styli/999/reset` and stylus "999" does not exist
- **THEN** the server SHALL respond with 404 status
