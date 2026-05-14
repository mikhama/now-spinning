## ADDED Requirements

### Requirement: Pi temperature API endpoint
The backend SHALL expose a `GET /temperature` endpoint that returns the Raspberry Pi CPU temperature in Celsius.

#### Scenario: Temperature endpoint returns valid data
- **WHEN** a GET request is made to `/temperature`
- **THEN** the response SHALL be JSON with a `celsius` float field (e.g., `{"celsius": 59.2}`)

#### Scenario: Temperature read from sysfs
- **WHEN** the backend reads Pi temperature
- **THEN** it SHALL read `/sys/class/thermal/thermal_zone0/temp` and divide by 1000 to get Celsius

#### Scenario: Temperature read failure
- **WHEN** the sysfs file is unavailable or unreadable (boardless mode or error)
- **THEN** the temperature endpoint SHALL return `{"celsius": null}` and log the error server-side

### Requirement: Pi temperature display in top bar
The top bar SHALL display the Pi CPU temperature in DM Mono at the design system's metadata size, colored `var(--ink-mute)`, formatted as "{value} °C" (integer, no decimal).

#### Scenario: Temperature renders in top bar
- **WHEN** the temperature is 59.2°C
- **THEN** the top bar SHALL display "59 °C" in ink-mute color

#### Scenario: Temperature updates periodically
- **WHEN** the UI is running
- **THEN** the temperature display SHALL update at least every 30 seconds

#### Scenario: Temperature unavailable
- **WHEN** the temperature value is null or fetch fails
- **THEN** the temperature display SHALL show "N/A"
