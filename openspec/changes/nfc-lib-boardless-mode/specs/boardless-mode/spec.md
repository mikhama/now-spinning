## ADDED Requirements

### Requirement: Boardless backend selection
The system SHALL select the boardless simulation backend when the environment variable `BOARDLESS_MODE` is set to `true`.

#### Scenario: Boardless mode activated
- **WHEN** the environment variable `BOARDLESS_MODE` is set to `true`
- **THEN** all `nfc_read()` and `nfc_write()` calls SHALL use the terminal-based simulation backend instead of real hardware

#### Scenario: Default to hardware mode
- **WHEN** the environment variable `BOARDLESS_MODE` is not set or set to `false`
- **THEN** the system SHALL use the real PN532 hardware backend

### Requirement: Boardless read simulation
The system SHALL prompt the user via terminal input to provide simulated card data when `nfc_read()` is called in boardless mode.

#### Scenario: User provides simulated read data
- **WHEN** `nfc_read()` is called in boardless mode
- **THEN** the system SHALL prompt the user to enter text via stdin and return that text as the read result

#### Scenario: User provides empty input for read
- **WHEN** `nfc_read()` is called in boardless mode and the user enters empty input
- **THEN** the function SHALL raise `NfcError`

### Requirement: Boardless write simulation
The system SHALL display the text being written and prompt the user for confirmation when `nfc_write()` is called in boardless mode.

#### Scenario: User confirms simulated write
- **WHEN** `nfc_write("Hello")` is called in boardless mode and the user confirms the write
- **THEN** the function SHALL return without error

#### Scenario: User rejects simulated write
- **WHEN** `nfc_write("Hello")` is called in boardless mode and the user does not confirm
- **THEN** the function SHALL raise `NfcError`
