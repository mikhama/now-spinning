## ADDED Requirements

### Requirement: Existing NFC backends can close safely
The library SHALL provide `Pn532Backend.close()` and `close_backend()`. Cleanup SHALL close only an existing backend and SHALL NOT initialize a reader. Repeated cleanup SHALL be safe, including after a cleanup error. Hardware close SHALL use the driver close method, which attempts RF-off and closes the transport after an RF-off error. Boardless cleanup SHALL have no hardware effects.

#### Scenario: No backend exists
- **WHEN** `close_backend()` is called before initialization
- **THEN** no reader SHALL be initialized and no hardware command SHALL start

#### Scenario: Close an initialized reader repeatedly
- **WHEN** cleanup is called more than once for an initialized reader
- **THEN** the driver close method SHALL run only once

#### Scenario: RF-off fails during close
- **WHEN** driver RF-off fails during backend close
- **THEN** the transport SHALL still close and the cleanup error SHALL remain available
- **AND** repeated cleanup SHALL NOT issue another hardware command

#### Scenario: Boardless cleanup
- **WHEN** the boardless backend closes
- **THEN** cleanup SHALL complete without a hardware command or user input

### Requirement: NFC diagnostics retain failure details
NFC error logs SHALL retain the original exception, error number, and failed transport stage through the exception chain. The I2C diagnostic SHALL report the actual bus error and SHALL NOT label every bus error as no acknowledgement.

#### Scenario: I2C transfer fails
- **WHEN** an I2C command write, ready-status read, ACK read, or response read fails
- **THEN** the logged exception chain SHALL identify the transport stage and original bus error number

#### Scenario: Diagnostic bus read fails
- **WHEN** the I2C diagnostic read raises an operating system error
- **THEN** the diagnostic SHALL print that error and its error number and close the bus
