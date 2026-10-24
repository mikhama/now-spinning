## MODIFIED Requirements

### Requirement: Standby NFC polling runs only in standby
The system SHALL perform real NFC scan polling only while the current UI mode is standby, including standby fallback states represented by standby errors. The coordinator SHALL default to a 200 ms detection timeout and retain a one-second RF-off pause after each operation, including successful record identification. Hardware commands SHALL remain serialized in the NFC worker. Entering a non-scanning mode SHALL prevent further standby scans; an already claimed operation SHALL finish bounded processing and RF-off cleanup before the worker becomes idle. Mode-change handlers SHALL NOT send hardware commands.

#### Scenario: Standby mode polls for NFC tag
- **WHEN** the current UI mode is standby
- **THEN** the system SHALL check for an NFC tag about once per second using at most 200 ms per detection probe
- **AND** it SHALL confirm RF-off before the one-second pause after the operation

#### Scenario: Non-standby mode does not poll
- **WHEN** the current UI mode is sync, link, re-link, stylus, or play
- **THEN** the system SHALL NOT perform the once-per-second standby NFC tag check
- **AND** RF SHALL remain off unless an explicitly requested NFC operation is active

#### Scenario: Standby error state remains polling-eligible
- **WHEN** the current UI mode is standby with `standbyError` set to `not-found` or `nfc`
- **THEN** the system SHALL treat the state as standby for NFC polling eligibility

#### Scenario: Mode changes during active standby attempt
- **WHEN** a standby attempt is already active and the mode changes to a non-scanning mode
- **THEN** the worker SHALL finish the bounded operation and RF-off cleanup before becoming idle
- **AND** it SHALL NOT start another standby attempt while that mode remains active
- **AND** it SHALL discard a late scan result or error event that would return the UI to Standby

## ADDED Requirements

### Requirement: Inactive modes keep NFC RF off
Play, Sync, Stylus, idle Link/Re-link, and every other mode without an active NFC operation SHALL keep RF off. Link/Re-link SHALL enable RF only for explicitly requested writes and their bounded probes, keep RF off between probes and after completion, and SHALL serialize writes with reads in the worker. Duplicate suppression, record replacement, last-record retention and event formats SHALL remain unchanged.

#### Scenario: Idle inactive modes
- **WHEN** Play, Sync, Stylus, Link/Re-link, or an unknown mode has no active NFC operation
- **THEN** RF SHALL remain off and no new standby probe SHALL begin

#### Scenario: Explicit Link or Re-link write
- **WHEN** an explicit write is requested in Link or Re-link
- **THEN** only the NFC worker SHALL execute it, using bounded RF-on probes and RF-off pauses
- **AND** RF SHALL be off after the complete write or any failure
