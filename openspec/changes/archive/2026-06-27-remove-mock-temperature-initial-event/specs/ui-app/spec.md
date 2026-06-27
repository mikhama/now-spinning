## MODIFIED Requirements

### Requirement: WebSocket connection for live updates
The UI SHALL establish a WebSocket connection to `/ws` and process incoming events to update the display in real time. WebSocket status events SHALL be ignored when a URL hash is present (dev mode). When no URL hash is present, a `status` event with `{"status": "play", "time": "MM:SS"}` SHALL transition the UI to Play mode, update the playback time shown in the top bar, and represent a spinning turntable. The UI SHALL NOT store a separate `spinning` payload field. A `status` event with `{"status": "stop"}` SHALL return the UI to Standby mode, represent a non-spinning turntable, and remove the Play-only playback time display. Temperature updates SHALL be driven by backend WebSocket `temperature_c` events rather than frontend polling.

#### Scenario: Receive stylus_hours event
- **WHEN** the WebSocket sends `{"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}}`
- **THEN** the UI SHALL update the stylus hours display

#### Scenario: Receive current_record event
- **WHEN** the WebSocket sends `{"event": "current_record", "data": {"record_id": "1"}}`
- **THEN** the UI SHALL update the current record display

#### Scenario: Receive temperature unavailable event
- **WHEN** the WebSocket sends `{"event": "temperature_c", "data": {"temp_c": null}}`
- **THEN** the UI SHALL update the temperature display to "N/A"

#### Scenario: Receive temperature reading event
- **WHEN** the WebSocket sends `{"event": "temperature_c", "data": {"temp_c": 59.2}}`
- **THEN** the UI SHALL update the temperature display to "59 °C"

#### Scenario: Receive status play event with time
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "play", "time": "00:01"}}` and no URL hash is present
- **THEN** the UI SHALL transition to Play mode
- **AND** the top bar SHALL render `PLAY 00:01`

#### Scenario: Receive status play event derives spinning state
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "play", "time": "03:30"}}` and no URL hash is present
- **THEN** the UI SHALL store the elapsed playback time
- **AND** the UI SHALL treat the turntable as spinning
- **AND** the UI SHALL NOT store a separate `spinning` payload value

#### Scenario: Receive status stop event
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "stop"}}` and no URL hash is present
- **THEN** the UI SHALL transition to Standby mode
- **AND** the top bar SHALL remove the Play-only playback time display

#### Scenario: Receive status event with hash
- **WHEN** the WebSocket sends a status event and a URL hash is present
- **THEN** the UI SHALL ignore the event and NOT change modes

#### Scenario: WebSocket reconnect
- **WHEN** the WebSocket connection closes
- **THEN** the UI SHALL attempt to reconnect every 3 seconds

### Requirement: REST API integration
The UI SHALL fetch record and stylus data from the API's REST endpoints on load. The UI SHALL NOT fetch `GET /temperature`; top-bar temperature state SHALL only reflect received WebSocket events.

#### Scenario: Initial data load
- **WHEN** the page loads
- **THEN** the UI SHALL fetch `GET /records` and `GET /styli` to populate local state
- **AND** the UI SHALL NOT fetch `GET /temperature`
