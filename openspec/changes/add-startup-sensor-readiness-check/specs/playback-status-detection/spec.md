## ADDED Requirements

### Requirement: RPM sensor startup readiness probe
The playback status detection module SHALL provide a startup readiness probe for the RPM sensor. The probe SHALL create the RPM reader using the same hardware initialization path as the runtime publisher, request one RPM sample, close the reader when possible, and raise an error when setup or sampling fails.

#### Scenario: RPM sensor readiness succeeds
- **WHEN** the RPM sensor readiness probe runs
- **AND** the RPM reader initializes successfully
- **AND** one RPM sample can be read
- **THEN** the readiness probe SHALL complete successfully
- **AND** the RPM reader SHALL be closed when it exposes a close operation

#### Scenario: RPM reader initialization fails readiness
- **WHEN** the RPM sensor readiness probe runs
- **AND** creating the RPM reader raises an error
- **THEN** the readiness probe SHALL raise an error
- **AND** startup SHALL be able to fail before the playback status publisher thread starts

#### Scenario: Initial RPM sample fails readiness
- **WHEN** the RPM sensor readiness probe runs
- **AND** creating the RPM reader succeeds
- **AND** reading the initial RPM sample raises an error
- **THEN** the readiness probe SHALL close the RPM reader when it exposes a close operation
- **AND** the readiness probe SHALL raise an error
