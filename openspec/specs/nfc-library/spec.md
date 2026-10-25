## Purpose
Provide a Python library for reading and writing text to NFC cards.

## Requirements

### Requirement: NFC read via library
The system SHALL provide a `nfc_read()` function in `lib.nfc` that waits for an NFC card and returns the text stored on it.

#### Scenario: Read text from a card in hardware mode
- **WHEN** `nfc_read()` is called with a real PN532 backend and a card is presented
- **THEN** the function SHALL return the text string stored on the card

#### Scenario: Read when no card is found
- **WHEN** `nfc_read()` is called and no card is detected within the timeout
- **THEN** the function SHALL raise `NfcError`

### Requirement: NFC write via library
The system SHALL provide a `nfc_write(text)` function in `lib.nfc` that waits for an NFC card and writes the given text to it.

#### Scenario: Write text to a card in hardware mode
- **WHEN** `nfc_write("Hello")` is called with a real PN532 backend and a card is presented
- **THEN** the function SHALL write the text to the card and return without error

#### Scenario: Write fails
- **WHEN** `nfc_write(text)` is called and the write operation fails (no card, error)
- **THEN** the function SHALL raise `NfcError`

### Requirement: NFC read attempt distinguishes no card from read failure
The system SHALL provide a hardware NFC read path that can attempt a short-timeout read and distinguish no-card absence from NFC read failure.

#### Scenario: Short read attempt finds a card
- **WHEN** a short NFC read attempt runs with a real PN532 backend and a supported card is presented
- **THEN** the read attempt SHALL return the text string stored on the card

#### Scenario: Short read attempt finds no card
- **WHEN** a short NFC read attempt runs and no card is detected before the timeout
- **THEN** the read attempt SHALL report no-card absence without treating it as an NFC read error

#### Scenario: Short read attempt encounters read failure
- **WHEN** a short NFC read attempt detects a card but authentication, page read, block read, or payload decoding fails
- **THEN** the read attempt SHALL report an NFC read error

### Requirement: NFC write stores exact record id text
The system SHALL write the exact selected record id string as the complete NFC tag text payload.

#### Scenario: Write numeric record id
- **WHEN** the system writes record id `1` to a supported NFC tag
- **THEN** the tag text payload SHALL be exactly `1`

#### Scenario: Write non-numeric record id
- **WHEN** the system writes record id `abc-123` to a supported NFC tag
- **THEN** the tag text payload SHALL be exactly `abc-123`

#### Scenario: Write does not store record metadata
- **WHEN** the system writes a selected record id to a supported NFC tag
- **THEN** the tag payload SHALL NOT include album title, artist, release id, master id, JSON, or any other record metadata

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
Detection SHALL enable RF for each probe and disable it after each unsuccessful probe. Repeated detection, including 30-second interactive write waits, SHALL pause RF-off for 500 ms between probes, capped by the remaining caller deadline. A found card SHALL retain RF through authentication and the complete payload read or write. Backend `finally` cleanup SHALL disable RF after success, timeout, failure, and interruption. RF-off failures SHALL be explicit `NfcError` failures and SHALL preserve any original operation failure in exception context. Public NFC signatures, tag payloads and boardless behavior SHALL remain compatible.

#### Scenario: Multi-page or multi-block transfer
- **WHEN** a detected card needs several page/block operations or authentications
- **THEN** RF SHALL remain enabled until all payload operations finish and SHALL then be disabled

#### Scenario: Repeated no-card detection
- **WHEN** a valid probe returns zero targets during a long wait
- **THEN** RF SHALL be disabled before a 500 ms pause and the next bounded probe

#### Scenario: Interrupted operation and cleanup failure
- **WHEN** an operation fails or is interrupted and RF-off also fails
- **THEN** cleanup SHALL report RF-off failure with the original operation failure retained in exception context

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
