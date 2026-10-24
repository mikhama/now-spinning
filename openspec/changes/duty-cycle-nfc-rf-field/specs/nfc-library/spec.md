## ADDED Requirements

### Requirement: PN532 RF lifecycle is explicit
Both I2C and UART drivers SHALL expose matching `set_rf_field(enabled: bool) -> bool` controls using RFConfiguration item `0x01` with `0x00` for off and `0x01` for on. Initialization SHALL configure passive activation retries to `0x00` (one attempt) and confirm RF-off before succeeding. Closing SHALL attempt RF-off and close the connection even when cleanup fails.

#### Scenario: Initialize either transport
- **WHEN** an I2C or UART driver initializes
- **THEN** it SHALL configure one passive activation attempt and receive a successful RF-off response before initialization completes

#### Scenario: Close after cleanup failure
- **WHEN** RF-off fails during driver close
- **THEN** the driver SHALL report an explicit `NfcError` and SHALL still close its transport

### Requirement: Detection uses bounded shared deadlines
Detection commands SHALL receive no more than 200 ms capped by the remaining caller timeout. Command transmission, ACK and response waits SHALL share one monotonic deadline. A valid zero-target reply SHALL mean absence; transport failure, timeout without a valid reply, malformed responses, and failed RF commands SHALL raise `NfcError`. Drivers SHALL await the expected response command, continue after ACKs, accept empty successful configuration responses, and reject stale responses.

#### Scenario: Delayed UART response after ACK
- **WHEN** an ACK arrives before a delayed expected response within the shared deadline
- **THEN** the driver SHALL keep waiting and return the expected payload, including an empty configuration payload

#### Scenario: Stale or malformed response
- **WHEN** the response belongs to another command or is malformed
- **THEN** it SHALL NOT be accepted as success or no-card absence
- **AND** the driver SHALL wait for the expected response within the original deadline or raise `NfcError`

#### Scenario: Nearly expired caller deadline
- **WHEN** less than 200 ms remains for detection
- **THEN** the detection command SHALL use only the remaining budget across ACK and response

### Requirement: RF stays on only for active NFC work
Detection SHALL enable RF for each probe and disable it after each unsuccessful probe. Repeated detection, including 30-second interactive write waits, SHALL pause RF-off for one second between probes, capped by the remaining caller deadline. A found card SHALL retain RF through authentication and the complete payload read or write. Backend `finally` cleanup SHALL disable RF after success, timeout, failure, and interruption. RF-off failures SHALL be explicit `NfcError` failures and SHALL preserve any original operation failure in exception context. Public NFC signatures, tag payloads and boardless behavior SHALL remain compatible.

#### Scenario: Multi-page or multi-block transfer
- **WHEN** a detected card needs several page/block operations or authentications
- **THEN** RF SHALL remain enabled until all payload operations finish and SHALL then be disabled

#### Scenario: Repeated no-card detection
- **WHEN** a valid probe returns zero targets during a long wait
- **THEN** RF SHALL be disabled before a one-second pause and the next bounded probe

#### Scenario: Interrupted operation and cleanup failure
- **WHEN** an operation fails or is interrupted and RF-off also fails
- **THEN** cleanup SHALL report RF-off failure with the original operation failure retained in exception context
