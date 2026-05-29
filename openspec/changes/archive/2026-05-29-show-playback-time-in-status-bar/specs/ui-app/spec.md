## MODIFIED Requirements

### Requirement: Persistent top bar
The UI SHALL display a persistent top bar across all modes with `background: var(--paper)`, `border-bottom: 2px solid var(--ink)`, showing the current mode label in DM Mono 11px uppercase on the left. In Play mode, when runtime state includes a playback time derived from a server `status` event, the left side SHALL render `PLAY {mm:ss}` with a single space separator. When no playback time is available, the left side SHALL render only the mode label. The right side SHALL contain a compact stylus wear bar (≈4rem × 0.5rem) followed by the Pi temperature in DM Mono 11px `color: var(--ink-mute)` format "{int} °C". The previous plain-text stylus hours display is removed from the top bar.

#### Scenario: Top bar displays mode label
- **WHEN** the current mode is "Standby"
- **THEN** the top bar SHALL show "STANDBY" in DM Mono uppercase on the left side with ink-colored text

#### Scenario: Top bar displays play time
- **WHEN** the current mode is "Play" and the current playback time is `00:01`
- **THEN** the top bar SHALL show `PLAY 00:01` on the left side

#### Scenario: Top bar omits play time when unavailable
- **WHEN** the current mode is "Play" and no playback time is available in runtime state
- **THEN** the top bar SHALL show `PLAY` with no trailing placeholder time

#### Scenario: Top bar displays compact stylus bar
- **WHEN** a stylus is loaded with 600 hours (capacity_max 1000)
- **THEN** the top bar right side SHALL show a compact progress bar filled to 60%

#### Scenario: Top bar hides compact bar when no styli
- **WHEN** no styli are loaded
- **THEN** the top bar SHALL hide the compact stylus bar entirely

#### Scenario: Top bar displays Pi temperature
- **WHEN** the Pi temperature is 59°C
- **THEN** the top bar right side SHALL show "59 °C" after the stylus bar, in DM Mono ink-mute color

### Requirement: WebSocket connection for live updates
The UI SHALL establish a WebSocket connection to `/ws` and process incoming events to update the display in real time. WebSocket status events SHALL be ignored when a URL hash is present (dev mode). When no URL hash is present, a `status` event with `{"status": "play", "time": "MM:SS"}` SHALL transition the UI to Play mode and update the playback time shown in the top bar. A `status` event with `{"status": "stop"}` SHALL return the UI to Standby mode and remove the Play-only playback time display.

#### Scenario: Receive stylus_hours event
- **WHEN** the WebSocket sends `{"event": "stylus_hours", "data": {"hours": 89.6, "stylus_id": "1"}}`
- **THEN** the UI SHALL update the stylus hours display

#### Scenario: Receive current_record event
- **WHEN** the WebSocket sends `{"event": "current_record", "data": {"record_id": "1"}}`
- **THEN** the UI SHALL update the current record display

#### Scenario: Receive status play event with time
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "play", "time": "00:01"}}` and no URL hash is present
- **THEN** the UI SHALL transition to Play mode
- **AND** the top bar SHALL render `PLAY 00:01`

#### Scenario: Receive status stop event
- **WHEN** the WebSocket sends `{"event": "status", "data": {"status": "stop"}}` and no URL hash is present
- **THEN** the UI SHALL transition out of Play mode
- **AND** the top bar SHALL stop rendering a playback time next to the mode label

#### Scenario: Receive status event with hash
- **WHEN** the WebSocket sends a status event and a URL hash is present
- **THEN** the UI SHALL ignore the event and NOT change modes

#### Scenario: WebSocket reconnect on disconnect
- **WHEN** the WebSocket connection is lost
- **THEN** the UI SHALL attempt to reconnect every 3 seconds