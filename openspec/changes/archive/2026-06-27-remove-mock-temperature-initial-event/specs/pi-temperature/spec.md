## ADDED Requirements

### Requirement: Backend temperature WebSocket publisher
The backend SHALL check the Raspberry Pi CPU temperature every 30 seconds and publish the result to connected WebSocket clients using `{"event": "temperature_c", "data": {"temp_c": <value-or-null>}}`.

#### Scenario: Periodic temperature broadcast succeeds
- **WHEN** the backend temperature publisher reads 59.2°C
- **THEN** the backend SHALL broadcast `{"event": "temperature_c", "data": {"temp_c": 59.2}}`

#### Scenario: Periodic temperature broadcast cannot read temperature
- **WHEN** the backend temperature publisher cannot read the sysfs temperature value
- **THEN** the backend SHALL broadcast `{"event": "temperature_c", "data": {"temp_c": null}}`
- **AND** the backend SHALL NOT substitute a mock temperature value

## REMOVED Requirements

### Requirement: Pi temperature API endpoint
**Reason**: Temperature is now delivered to the frontend through backend-owned WebSocket events, so a frontend-callable REST temperature endpoint is no longer needed.
**Migration**: Use the backend `temperature_c` WebSocket event with nullable `temp_c` payloads.

## MODIFIED Requirements

### Requirement: Pi temperature display in top bar
The top bar SHALL display the Pi CPU temperature in DM Mono at the design system's metadata size, colored `var(--ink-mute)`, formatted as "{value} °C" (integer, no decimal). Temperature updates SHALL come from backend WebSocket `temperature_c` events.

#### Scenario: Temperature renders in top bar
- **WHEN** the temperature is 59.2°C
- **THEN** the top bar SHALL display "59 °C" in ink-mute color

#### Scenario: Temperature updates periodically
- **WHEN** the UI is running and the backend publishes periodic `temperature_c` events
- **THEN** the temperature display SHALL update at least every 30 seconds

#### Scenario: Temperature unavailable
- **WHEN** the temperature value is null
- **THEN** the temperature display SHALL show "N/A"
