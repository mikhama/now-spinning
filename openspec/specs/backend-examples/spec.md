## Purpose
Provide backend examples demonstrating NFC library usage.

## Requirements

### Requirement: Backend main with NFC examples
The system SHALL provide a `backend/main.py` file with simple examples demonstrating how to use the NFC library functions.

#### Scenario: Run backend main in boardless mode
- **WHEN** the user runs `python -m backend.main` with `BOARDLESS_MODE=true`
- **THEN** the application SHALL present a menu with options to read an NFC tag, write an NFC tag, or quit, using the boardless simulation backend

#### Scenario: Read example via menu
- **WHEN** the user selects the "read" option from the menu
- **THEN** the application SHALL call `nfc_read()` and display the result

#### Scenario: Write example via menu
- **WHEN** the user selects the "write" option from the menu
- **THEN** the application SHALL prompt for text, call `nfc_write(text)`, and display whether the write succeeded
