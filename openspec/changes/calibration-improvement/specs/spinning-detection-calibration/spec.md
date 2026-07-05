## MODIFIED Requirements

### Requirement: Threshold-based timing start
The calibration script SHALL sample the platter sensor and start the tonearm delay timer only after the measured RPM is above `1000` and has increased by more than `500` RPM across a `3` second observation window.

#### Scenario: Sensor value is below minimum RPM
- **WHEN** the latest measured RPM is `1000` or lower
- **THEN** the script SHALL continue sampling and SHALL NOT start the tonearm delay timer

#### Scenario: Sensor value has not increased enough
- **WHEN** the latest measured RPM is above `1000`
- **AND** the RPM increase across the `3` second observation window is `500` RPM or less
- **THEN** the script SHALL continue sampling and SHALL NOT start the tonearm delay timer

#### Scenario: Sensor value reaches spin-up trend
- **WHEN** the latest measured RPM is above `1000`
- **AND** the RPM has increased by more than `500` RPM across the `3` second observation window
- **THEN** the script SHALL start the tonearm delay timer and print a console message telling the operator that timing has started

## ADDED Requirements

### Requirement: Calibration stopped detection
The calibration script SHALL classify the platter as stopped when the latest measured RPM is below `1000`, or when the latest `4` consecutive RPM readings are strictly decreasing and the total drop from the first reading to the fourth reading is at least `1000` RPM.

#### Scenario: RPM drops below stopped threshold
- **WHEN** the latest measured RPM is below `1000`
- **THEN** the script SHALL classify the platter as stopped

#### Scenario: RPM constantly decreases with sufficient total drop
- **WHEN** the latest `4` consecutive RPM readings are strictly decreasing
- **AND** the total drop from the first reading to the fourth reading is at least `1000` RPM
- **THEN** the script SHALL classify the platter as stopped

#### Scenario: RPM does not constantly decrease
- **WHEN** the latest `4` consecutive RPM readings are not strictly decreasing
- **AND** the latest measured RPM is `1000` or higher
- **THEN** the script SHALL NOT classify the platter as stopped from those readings

#### Scenario: RPM constantly decreases without sufficient total drop
- **WHEN** the latest `4` consecutive RPM readings are strictly decreasing
- **AND** the total drop from the first reading to the fourth reading is less than `1000` RPM
- **AND** the latest measured RPM is `1000` or higher
- **THEN** the script SHALL NOT classify the platter as stopped from those readings
