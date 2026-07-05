## Purpose

Define the experimental calibration behavior for deriving platter spinning detection constants on target turntable hardware.

## Requirements

### Requirement: Experimental calibration script location
The system SHALL provide an experimental console calibration script under `exp/` for deriving spinning detection constants on the target turntable hardware.

#### Scenario: Operator finds the calibration helper
- **WHEN** a developer inspects the `exp/` directory
- **THEN** the calibration script is present alongside the existing platter spinning experiment code

### Requirement: Manual spinning threshold constant
The calibration script SHALL expose the spinning threshold as a manually editable constant in the script.

#### Scenario: Operator configures the threshold before running
- **WHEN** an operator opens the calibration script before a run
- **THEN** the spinning threshold value is visible as a top-level constant that can be edited directly

### Requirement: Threshold-based timing start
The calibration script SHALL sample the platter sensor and start the tonearm delay timer only after the measured RPM is above `1000` and either has increased by more than `500` RPM across a `3` second observation window, or both the latest and comparison RPM are above `1000`, have stayed within `500` RPM increase/decrease across that window, and the window is not strictly decreasing.

#### Scenario: Sensor value is below minimum RPM
- **WHEN** the latest measured RPM is `1000` or lower
- **THEN** the script SHALL continue sampling and SHALL NOT start the tonearm delay timer

#### Scenario: Sensor value is decreasing too much
- **WHEN** the latest measured RPM is above `1000`
- **AND** the RPM decrease across the `3` second observation window is more than `500` RPM
- **THEN** the script SHALL continue sampling and SHALL NOT start the tonearm delay timer

#### Scenario: Sensor value reaches spin-up trend
- **WHEN** the latest measured RPM is above `1000`
- **AND** the RPM has increased by more than `500` RPM across the `3` second observation window
- **THEN** the script SHALL start the tonearm delay timer and print a console message telling the operator that timing has started

#### Scenario: Sensor value is already spinning steadily
- **WHEN** the latest measured RPM is above `1000`
- **AND** the comparison RPM from the `3` second observation window is above `1000`
- **AND** the RPM change across the `3` second observation window is no more than `500` RPM increase or decrease
- **AND** the readings across the `3` second observation window are not strictly decreasing
- **THEN** the script SHALL start the tonearm delay timer and print a console message telling the operator that timing has started

#### Scenario: Sensor value is steadily decreasing
- **WHEN** the latest measured RPM is above `1000`
- **AND** the RPM change across the `3` second observation window is no more than `500` RPM increase or decrease
- **AND** the readings across the `3` second observation window are strictly decreasing
- **THEN** the script SHALL continue sampling and SHALL NOT start the tonearm delay timer

### Requirement: Calibration stopped detection
The calibration script SHALL classify the platter as stopped when the latest measured RPM is below `1000`, or when the latest strictly decreasing run contains at least `4` consecutive RPM readings and the total drop from the first reading in that run to the latest reading is at least `1000` RPM.

#### Scenario: RPM drops below stopped threshold
- **WHEN** the latest measured RPM is below `1000`
- **THEN** the script SHALL classify the platter as stopped

#### Scenario: RPM constantly decreases with sufficient total drop
- **WHEN** the latest strictly decreasing run contains at least `4` consecutive RPM readings
- **AND** the total drop from the first reading in that run to the latest reading is at least `1000` RPM
- **THEN** the script SHALL classify the platter as stopped

#### Scenario: RPM gradually decreases over more than the spin-up observation window
- **WHEN** stop-detection mode samples a latest strictly decreasing run longer than `3` seconds
- **AND** the total drop from the first reading in that run to the latest reading is at least `1000` RPM
- **THEN** the script SHALL preserve the run and classify the platter as stopped

#### Scenario: RPM does not constantly decrease
- **WHEN** the latest strictly decreasing run contains fewer than `4` consecutive RPM readings
- **AND** the latest measured RPM is `1000` or higher
- **THEN** the script SHALL NOT classify the platter as stopped from those readings

#### Scenario: RPM constantly decreases without sufficient total drop
- **WHEN** the latest strictly decreasing run contains at least `4` consecutive RPM readings
- **AND** the total drop from the first reading in that run to the latest reading is less than `1000` RPM
- **AND** the latest measured RPM is `1000` or higher
- **THEN** the script SHALL NOT classify the platter as stopped from those readings

### Requirement: Manual needle-on-platter stop
The calibration script SHALL wait for the operator to press Enter when they see the needle reach the platter.

#### Scenario: Operator confirms needle on platter
- **WHEN** the tonearm delay timer is running and the operator presses Enter
- **THEN** the script stops the timer

### Requirement: Elapsed timing result
The calibration script SHALL print the elapsed tonearm delay in milliseconds after the operator confirms that the needle has reached the platter.

#### Scenario: Calibration run completes
- **WHEN** the operator presses Enter after the timer has started
- **THEN** the script prints the measured elapsed time in milliseconds for use as the calibration constant
