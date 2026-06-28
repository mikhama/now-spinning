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
