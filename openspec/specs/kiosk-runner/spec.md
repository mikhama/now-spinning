# kiosk-runner Specification

## Purpose
Defines the repository-local kiosk launch script for starting the app on a Raspberry Pi touchscreen with Chromium in kiosk mode.

## Requirements
### Requirement: Kiosk script entry point
The system SHALL provide an executable `./bin/run_kiosk.sh` script that can be run from the repository root to start kiosk mode using the repository virtualenv at `env/`.

#### Scenario: User starts kiosk mode from repository root
- **WHEN** the user runs `./bin/run_kiosk.sh`
- **THEN** the script activates `env/` and starts the app using the existing app entry point

#### Scenario: Project virtualenv is unavailable
- **WHEN** `env/bin/activate` is missing
- **THEN** the script exits with a clear error explaining that the project virtualenv is required

### Requirement: App startup readiness
The kiosk script SHALL wait until the app is reachable at `http://127.0.0.1:5000/` before opening the browser.

#### Scenario: Browser opens after server is ready
- **WHEN** the script starts the app process
- **THEN** the script waits for the HTTP endpoint to respond before launching Chromium

### Requirement: Chromium kiosk launch
The kiosk script SHALL launch `chromium` in kiosk mode pointed at `http://127.0.0.1:5000/`.

#### Scenario: Chromium is available
- **WHEN** `chromium` is available on `PATH` and the app is ready
- **THEN** the script launches Chromium with kiosk flags for the local app URL

#### Scenario: Chromium is unavailable
- **WHEN** `chromium` is not available on `PATH`
- **THEN** the script exits with a clear error explaining that Chromium is required

### Requirement: Process cleanup
The kiosk script SHALL stop the app process it started when the script exits or receives a common interrupt signal.

#### Scenario: User interrupts the kiosk script
- **WHEN** the user interrupts the running script
- **THEN** the script terminates the app process it started

### Requirement: README kiosk note
The README SHALL document the kiosk command with a short usage note.

#### Scenario: User reads usage documentation
- **WHEN** the user reads the README usage section
- **THEN** the README shows `./bin/run_kiosk.sh` as the command for running the app in kiosk mode
