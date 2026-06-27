## MODIFIED Requirements

### Requirement: Process cleanup
The kiosk script SHALL stop the app process and Chromium process it started when the script exits or receives a common interrupt signal. When the app receives a UI-triggered kiosk exit request, the kiosk script SHALL exit through the same cleanup path.

#### Scenario: User interrupts the kiosk script
- **WHEN** the user interrupts the running script
- **THEN** the script terminates the app process it started
- **AND** the script terminates the Chromium process it started

#### Scenario: User exits from kiosk UI
- **WHEN** the user confirms kiosk exit from the UI
- **THEN** the kiosk script terminates the app process it started
- **AND** the kiosk script terminates the Chromium process it started
