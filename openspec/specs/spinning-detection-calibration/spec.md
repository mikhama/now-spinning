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
The calibration script SHALL sample the platter sensor and start the tonearm delay timer only after the measured spinning value reaches or exceeds the configured threshold.

#### Scenario: Sensor value is below threshold
- **WHEN** the measured spinning value is below the configured threshold
- **THEN** the script continues sampling and does not start the tonearm delay timer

#### Scenario: Sensor value reaches threshold
- **WHEN** the measured spinning value reaches or exceeds the configured threshold
- **THEN** the script starts the tonearm delay timer and prints a console message telling the operator that timing has started

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
