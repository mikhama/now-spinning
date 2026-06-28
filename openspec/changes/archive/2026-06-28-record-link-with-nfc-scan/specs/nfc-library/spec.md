## ADDED Requirements

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
