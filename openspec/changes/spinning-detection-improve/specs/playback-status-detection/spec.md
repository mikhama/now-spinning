## MODIFIED Requirements

### Requirement: Play detection after threshold and tonearm delay
The backend SHALL consider the record playing only after runtime spin-up detection succeeds and `TONEARM_DELAY_AUTO = 12065` milliseconds has elapsed since that spin-up detection. Runtime spin-up detection SHALL succeed when the latest measured RPM is above `1000` and either has increased by more than `500` RPM across a `3` second observation window, or both the latest and comparison RPM are above `1000`, have stayed within `500` RPM increase/decrease across that window, and the window is not strictly decreasing.

#### Scenario: RPM below minimum spinning value is not playing
- **WHEN** the latest sampled RPM value is `1000` or lower
- **THEN** the backend SHALL NOT consider the record playing
- **AND** the backend SHALL NOT emit a play status event

#### Scenario: Insufficient spin-up increase does not start tonearm delay
- **WHEN** the latest sampled RPM value is above `1000`
- **AND** the RPM has not increased by more than `500` RPM across the `3` second observation window
- **AND** the comparison RPM from that observation window is `1000` or lower
- **THEN** the backend SHALL NOT start the tonearm delay timer
- **AND** the backend SHALL NOT emit a play status event

#### Scenario: Spin-up trend starts tonearm delay
- **WHEN** the latest sampled RPM value is above `1000`
- **AND** the RPM has increased by more than `500` RPM across the `3` second observation window
- **THEN** the backend SHALL start the tonearm delay timer for that spin-up detection
- **AND** the backend SHALL NOT emit a play status event before `12065` milliseconds has elapsed

#### Scenario: Already-spinning steady RPM starts tonearm delay
- **WHEN** the latest sampled RPM value is above `1000`
- **AND** the comparison RPM from the `3` second observation window is above `1000`
- **AND** the RPM change across the `3` second observation window is no more than `500` RPM increase or decrease
- **AND** the readings across the `3` second observation window are not strictly decreasing
- **THEN** the backend SHALL start the tonearm delay timer for that spin-up detection
- **AND** the backend SHALL NOT emit a play status event before `12065` milliseconds has elapsed

#### Scenario: Strictly decreasing steady-range RPM does not start tonearm delay
- **WHEN** the latest sampled RPM value is above `1000`
- **AND** the RPM change across the `3` second observation window is no more than `500` RPM increase or decrease
- **AND** the readings across the `3` second observation window are strictly decreasing
- **THEN** the backend SHALL NOT start the tonearm delay timer
- **AND** the backend SHALL NOT emit a play status event

#### Scenario: Tonearm delay completion starts playback
- **WHEN** runtime spin-up detection has started the tonearm delay timer
- **AND** runtime stopped detection has not reset the pending playback
- **AND** `12065` milliseconds has elapsed since spin-up detection
- **THEN** the backend SHALL consider the record playing
- **AND** the backend SHALL emit a play status event with elapsed playback time `00:00`

#### Scenario: Active playback emits elapsed time updates
- **WHEN** the backend considers the record playing
- **AND** runtime stopped detection has not classified the platter as stopped
- **AND** the elapsed playback second advances
- **THEN** the backend SHALL emit a play status event with `time` formatted as zero-padded `MM:SS`

#### Scenario: Stopped detection before tonearm delay completes
- **WHEN** runtime spin-up detection has started the tonearm delay timer
- **AND** runtime stopped detection later classifies the platter as stopped before `12065` milliseconds has elapsed
- **THEN** the backend SHALL reset the pending tonearm delay
- **AND** the backend SHALL NOT emit a play status event for that incomplete spin-up detection

### Requirement: Stop detection below threshold
The backend SHALL consider the record stopped playing when runtime stopped detection succeeds after the record was considered playing. Runtime stopped detection SHALL succeed when the latest measured RPM is below `1000`, or when the latest strictly decreasing run contains at least `4` consecutive RPM readings and the total drop from the first reading in that run to the latest reading is at least `1000` RPM.

#### Scenario: RPM drops below stopped threshold after playback started
- **WHEN** the backend considers the record playing
- **AND** the latest sampled RPM value is below `1000`
- **THEN** the backend SHALL consider the record stopped playing
- **AND** the backend SHALL emit one stop status event

#### Scenario: Strictly decreasing run stops playback
- **WHEN** the backend considers the record playing
- **AND** the latest strictly decreasing run contains at least `4` consecutive RPM readings
- **AND** the total drop from the first reading in that run to the latest reading is at least `1000` RPM
- **THEN** the backend SHALL consider the record stopped playing
- **AND** the backend SHALL emit one stop status event

#### Scenario: Non-stopped samples keep playback active
- **WHEN** the backend considers the record playing
- **AND** the latest sampled RPM value is `1000` or higher
- **AND** the latest strictly decreasing run contains fewer than `4` consecutive RPM readings or has a total drop less than `1000` RPM
- **THEN** the backend SHALL continue considering the record playing
- **AND** the backend SHALL NOT emit a stop status event

### Requirement: Status event deduplication
The backend SHALL suppress duplicate play-time and stop status events while preserving elapsed playback time updates.

#### Scenario: Repeated playing samples in the same second do not repeat play
- **WHEN** the backend has already emitted a play status event for the current elapsed playback second
- **AND** later sampled RPM values have not triggered runtime stopped detection in that same elapsed second
- **THEN** the backend SHALL NOT emit an additional play status event for that same second

#### Scenario: Repeated stopped samples do not repeat stop
- **WHEN** the backend has already emitted a stop status event for the current playback interval
- **AND** later sampled RPM values still classify as stopped
- **THEN** the backend SHALL NOT emit additional stop status events
