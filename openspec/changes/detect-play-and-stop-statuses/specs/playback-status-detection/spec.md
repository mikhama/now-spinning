## ADDED Requirements

### Requirement: RPM polling cadence
The backend SHALL sample platter RPM once per second while playback status detection is running.

#### Scenario: Runtime detector polls RPM
- **WHEN** playback status detection is running
- **THEN** the backend SHALL request a new RPM sample every one second

### Requirement: Play detection after threshold and tonearm delay
The backend SHALL consider the record playing only after RPM reaches or exceeds `SPINNING_RPM_THRESHOLD = 5500` and `TONEARM_DELAY_AUTO = 9726` milliseconds has elapsed since that threshold crossing.

#### Scenario: RPM below threshold is not playing
- **WHEN** a sampled RPM value is below `5500`
- **THEN** the backend SHALL NOT consider the record playing
- **AND** the backend SHALL NOT emit a play status event

#### Scenario: Threshold crossing starts tonearm delay
- **WHEN** a sampled RPM value reaches or exceeds `5500`
- **THEN** the backend SHALL start the tonearm delay timer for that threshold crossing
- **AND** the backend SHALL NOT emit a play status event before `9726` milliseconds has elapsed

#### Scenario: Tonearm delay completion starts playback
- **WHEN** RPM has reached or exceeded `5500`
- **AND** `9726` milliseconds has elapsed since the threshold crossing
- **THEN** the backend SHALL consider the record playing
- **AND** the backend SHALL emit one play status event

#### Scenario: RPM drops before tonearm delay completes
- **WHEN** RPM reaches or exceeds `5500`
- **AND** RPM later falls below `5500` before `9726` milliseconds has elapsed
- **THEN** the backend SHALL reset the pending tonearm delay
- **AND** the backend SHALL NOT emit a play status event for that incomplete threshold crossing

### Requirement: Stop detection below threshold
The backend SHALL consider the record stopped playing when RPM falls below `SPINNING_RPM_THRESHOLD = 5500` after the record was considered playing.

#### Scenario: RPM drops after playback started
- **WHEN** the backend considers the record playing
- **AND** a sampled RPM value falls below `5500`
- **THEN** the backend SHALL consider the record stopped playing
- **AND** the backend SHALL emit one stop status event

#### Scenario: RPM stays above threshold during playback
- **WHEN** the backend considers the record playing
- **AND** sampled RPM values remain at or above `5500`
- **THEN** the backend SHALL continue considering the record playing
- **AND** the backend SHALL NOT emit a stop status event

### Requirement: Status event deduplication
The backend SHALL emit play and stop status events only when the detected playback state changes.

#### Scenario: Repeated playing samples do not repeat play
- **WHEN** the backend has already emitted a play status event for the current playback interval
- **AND** later sampled RPM values remain at or above `5500`
- **THEN** the backend SHALL NOT emit additional play status events

#### Scenario: Repeated stopped samples do not repeat stop
- **WHEN** the backend has already emitted a stop status event for the current playback interval
- **AND** later sampled RPM values remain below `5500`
- **THEN** the backend SHALL NOT emit additional stop status events
