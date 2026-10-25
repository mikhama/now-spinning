## ADDED Requirements

### Requirement: NFC worker shutdown is terminal and owns cleanup
When shutdown starts, the NFC worker SHALL reject new operations, discard queued work, and let its active operation finish. The polling pause SHALL be interruptible. The worker SHALL close the reader in its `finally` block and record cleanup success or failure. Mode changes SHALL NOT restart work after shutdown starts. Hardware commands SHALL remain in the worker, including reader close.

#### Scenario: Stop during idle polling
- **WHEN** shutdown starts during a polling pause
- **THEN** the worker SHALL wake, close the reader, and exit

#### Scenario: Stop during a read
- **WHEN** shutdown starts during a Standby read with a queued write
- **THEN** the active read SHALL finish before reader close and the queued write SHALL NOT start
- **AND** a failed read SHALL preserve the last successful record

#### Scenario: Stop during a confirmed write
- **WHEN** an active write succeeds within the shutdown wait
- **THEN** the worker SHALL keep its existing persistence and completion event behavior before reader close

### Requirement: Application cleanup has one bounded NFC wait
The application SHALL retain its NFC thread reference and use one cleanup path for termination signals, normal server exit, startup failure, and process-exit cleanup. It SHALL request worker shutdown and wait up to five seconds, including reader close. If the worker remains active, it SHALL log incomplete cleanup and continue exit without a competing reader command. Repeated cleanup calls and signals SHALL be safe. If startup fails before the worker starts, cleanup SHALL close an initialized reader without initializing another reader. Stylus persistence checks and the existing Exit response SHALL remain in effect.

#### Scenario: Terminate during a Standby read
- **WHEN** the application receives SIGTERM during a Standby read that finishes within five seconds
- **THEN** reader cleanup SHALL complete before normal process exit

#### Scenario: Worker stays blocked
- **WHEN** an active read, write, or reader close remains blocked for five seconds
- **THEN** application cleanup SHALL report incomplete cleanup and return without another hardware command

#### Scenario: Startup fails after reader initialization
- **WHEN** a later startup check fails before the worker starts
- **THEN** cleanup SHALL close the existing reader and preserve the startup failure

#### Scenario: Cleanup paths repeat
- **WHEN** signals, server cleanup, or process-exit cleanup run more than once
- **THEN** they SHALL NOT repeat reader close or extend the NFC shutdown wait

### Requirement: NFC requests report shutdown
New NFC mode and write requests during shutdown SHALL return JSON with HTTP status 503. The coordinator SHALL also reject requests that race with shutdown.

#### Scenario: Request arrives after stop
- **WHEN** `/nfc/mode` or `/nfc/write` receives a request after shutdown starts
- **THEN** it SHALL return JSON 503 and SHALL NOT queue work

### Requirement: NFC lifecycle logs distinguish operation and cleanup failures
The application SHALL log NFC mode transitions, operation outcomes, and shutdown results. Failure logs SHALL include the exception chain. Local validation and Pi validation SHALL be reported separately. A hardware fix SHALL be confirmed only after the user verifies the application on the Pi after deployment. The reported sequences are Scan → play → stop → Standby → Exit → reopen and scan 1 → 43 → 15 → 23 → 1 → Exit → reopen.

#### Scenario: Read fails before shutdown
- **WHEN** a read fails and the application later exits
- **THEN** logs SHALL identify the read failure separately from the reader cleanup result

#### Scenario: Hardware validation remains pending
- **WHEN** only local tests have passed
- **THEN** the verification record SHALL state that the Pi restart fault is not yet verified as fixed
