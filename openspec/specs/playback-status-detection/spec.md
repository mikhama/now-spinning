# playback-status-detection Specification

## Purpose
Define backend playback status detection from platter RPM readings.

## Requirements
### Requirement: RPM polling cadence
The backend SHALL sample platter RPM once per second while playback status detection is running.

#### Scenario: Runtime detector polls RPM
- **WHEN** playback status detection is running
- **THEN** the backend SHALL request a new RPM sample every one second

### Requirement: Play detection after threshold and tonearm delay
The backend SHALL consider the record playing only after RPM reaches or exceeds `SPINNING_RPM_THRESHOLD = 4500` and `TONEARM_DELAY_AUTO = 10713` milliseconds has elapsed since that threshold crossing.

#### Scenario: RPM below threshold is not playing
- **WHEN** a sampled RPM value is below `4500`
- **THEN** the backend SHALL NOT consider the record playing
- **AND** the backend SHALL NOT emit a play status event

#### Scenario: Threshold crossing starts tonearm delay
- **WHEN** a sampled RPM value reaches or exceeds `4500`
- **THEN** the backend SHALL start the tonearm delay timer for that threshold crossing
- **AND** the backend SHALL NOT emit a play status event before `10713` milliseconds has elapsed

#### Scenario: Tonearm delay completion starts playback
- **WHEN** RPM has reached or exceeded `4500`
- **AND** `10713` milliseconds has elapsed since the threshold crossing
- **THEN** the backend SHALL consider the record playing
- **AND** the backend SHALL emit a play status event with elapsed playback time `00:00`

#### Scenario: Active playback emits elapsed time updates
- **WHEN** the backend considers the record playing
- **AND** sampled RPM values remain at or above `4500`
- **AND** the elapsed playback second advances
- **THEN** the backend SHALL emit a play status event with `time` formatted as zero-padded `MM:SS`

#### Scenario: RPM drops before tonearm delay completes
- **WHEN** RPM reaches or exceeds `4500`
- **AND** RPM later falls below `4500` before `10713` milliseconds has elapsed
- **THEN** the backend SHALL reset the pending tonearm delay
- **AND** the backend SHALL NOT emit a play status event for that incomplete threshold crossing

### Requirement: Stop detection below threshold
The backend SHALL consider the record stopped playing when RPM falls below `SPINNING_RPM_THRESHOLD = 4500` after the record was considered playing.

#### Scenario: RPM drops after playback started
- **WHEN** the backend considers the record playing
- **AND** a sampled RPM value falls below `4500`
- **THEN** the backend SHALL consider the record stopped playing
- **AND** the backend SHALL emit one stop status event

#### Scenario: RPM stays above threshold during playback
- **WHEN** the backend considers the record playing
- **AND** sampled RPM values remain at or above `4500`
- **THEN** the backend SHALL continue considering the record playing
- **AND** the backend SHALL NOT emit a stop status event

### Requirement: Status event deduplication
The backend SHALL suppress duplicate play-time and stop status events while preserving elapsed playback time updates.

#### Scenario: Repeated playing samples in the same second do not repeat play
- **WHEN** the backend has already emitted a play status event for the current elapsed playback second
- **AND** later sampled RPM values remain at or above `4500` in that same elapsed second
- **THEN** the backend SHALL NOT emit an additional play status event for that same second

#### Scenario: Repeated stopped samples do not repeat stop
- **WHEN** the backend has already emitted a stop status event for the current playback interval
- **AND** later sampled RPM values remain below `4500`
- **THEN** the backend SHALL NOT emit additional stop status events
