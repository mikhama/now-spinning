## MODIFIED Requirements

### Requirement: WebSocket endpoint with initial events
The system SHALL provide a WebSocket endpoint that sends initial state events upon connection. The initial temperature event SHALL always represent the current runtime temperature state and SHALL use `temp_c: null` when no real backend temperature reading is available. The server SHALL NOT send a mocked temperature value. An externally supplied null scan that occurs after a successful non-null scan or established current record SHALL NOT replace the last resolved record event in the runtime snapshot sent to newly connected clients. A null scan error before any such success SHALL be available as the startup NFC error snapshot.

#### Scenario: Client connects before a temperature reading exists
- **WHEN** a client establishes a WebSocket connection before any backend temperature read has succeeded
- **THEN** the server SHALL send `{"event": "temperature_c", "data": {"temp_c": null}}`
- **AND** the server SHALL NOT send a mocked numeric temperature value

#### Scenario: Client connects after a temperature reading exists
- **WHEN** a client establishes a WebSocket connection after the backend has read a temperature of 59.2°C
- **THEN** the server SHALL send `{"event": "temperature_c", "data": {"temp_c": 59.2}}`

#### Scenario: Client connects after a startup NFC error
- **WHEN** a null scan error occurred before any successful non-null scan or current record
- **AND** a client establishes a WebSocket connection
- **THEN** the server SHALL seed the client with `{"event":"scan","data":{"record_id":null}}`

#### Scenario: Client reconnects after a successful scan and later external null event
- **WHEN** a non-null scan for record id `1` was broadcast and a later external null scan was broadcast
- **AND** a client establishes a WebSocket connection
- **THEN** the server SHALL seed the client with `{"event":"scan","data":{"record_id":"1"}}`
- **AND** the server SHALL NOT seed the client with the later null scan

#### Scenario: Client reconnects after an established current record and later external null event
- **WHEN** a `current_record` event established record id `1` and a later external null scan was broadcast
- **AND** a client establishes a WebSocket connection
- **THEN** the server SHALL seed the client with `{"event":"current_record","data":{"record_id":"1"}}`
- **AND** the server SHALL NOT seed the client with the later null scan
