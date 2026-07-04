# stylus-hours-tracking Specification

## Purpose
Tracks stylus playback usage in memory and persists accumulated hours at defined flush points.

## Requirements
### Requirement: Backend tracks active stylus playback time
The backend SHALL accrue stylus usage time while playback status is `play`, using the active stylus from persisted stylus data as the counted stylus.

#### Scenario: Playback time accrues for active stylus
- **WHEN** the backend has an active stylus with 100.0 persisted hours
- **AND** playback status events advance from `00:00` to `10:00`
- **THEN** the backend SHALL accrue 600 seconds of usage for that stylus
- **AND** the current runtime stylus hours SHALL become approximately 100.1667 hours

#### Scenario: No active stylus skips accrual
- **WHEN** playback status events indicate active playback
- **AND** no stylus is available from persisted stylus data
- **THEN** the backend SHALL NOT create a stylus row
- **AND** the backend SHALL NOT emit a `stylus_hours` event for a missing stylus

### Requirement: Backend publishes live stylus hours
The backend SHALL publish `stylus_hours` WebSocket events as playback accrues so connected clients can display the current in-memory stylus usage before the next durable flush.

#### Scenario: Playback emits stylus hours update
- **WHEN** playback status advances for an active stylus
- **THEN** the backend SHALL broadcast `{"event": "stylus_hours", "data": {"stylus_id": "<id>", "hours": <current-hours>}}`
- **AND** the backend SHALL update runtime state for newly connected WebSocket clients

### Requirement: Backend flushes accumulated stylus hours periodically
The backend SHALL persist accumulated stylus playback time at least once for every 600 seconds of unflushed active playback.

#### Scenario: Ten minutes of playback triggers flush
- **WHEN** an active stylus has unflushed playback usage
- **AND** playback status reaches 600 seconds beyond the last stylus-hour flush
- **THEN** the backend SHALL persist the accumulated delta to the stylus row
- **AND** the backend SHALL clear the flushed pending usage from memory

#### Scenario: Less than ten minutes remains pending
- **WHEN** an active stylus has 599 seconds of unflushed playback usage
- **AND** playback continues
- **THEN** the backend SHALL keep those seconds pending in memory
- **AND** the backend SHALL NOT perform the periodic flush yet

### Requirement: Backend flushes accumulated stylus hours on playback stop
The backend SHALL persist all pending active stylus playback usage when playback status changes from `play` to `stop`.

#### Scenario: Stop flushes short play
- **WHEN** an active stylus has 240 seconds of unflushed playback usage
- **AND** the backend receives a `status` event with `status: "stop"`
- **THEN** the backend SHALL persist the 240 second usage delta to the stylus row
- **AND** no pending usage for that playback interval SHALL remain in memory

### Requirement: Stylus reset clears pending usage
When a stylus is reset, the backend SHALL align runtime tracking with the reset value and discard pending unflushed usage for that stylus.

#### Scenario: Reset active stylus during playback
- **WHEN** an active stylus has pending unflushed playback usage
- **AND** the stylus reset endpoint successfully persists `distance_hours = 0`
- **THEN** runtime stylus hours for that stylus SHALL be `0`
- **AND** pending unflushed usage for that stylus SHALL be cleared
