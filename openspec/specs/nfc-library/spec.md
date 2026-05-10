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
