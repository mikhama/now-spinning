## ADDED Requirements

### Requirement: One committed-history console report
The standard-library-only executable `./bin/sessions-history` SHALL read committed entries chronologically, with primary key tie-breaking, and combine consecutive entries of the same local record ID regardless of gap. It SHALL use the first start and sum only recorded durations. A → B → A SHALL remain three rows; different albums by one artist SHALL remain separate. Unknown playback SHALL not be stored or create separators.

#### Scenario: Summed example with large gaps
- **WHEN** consecutive A entries contain 600, 600, and 34 seconds followed by B entries containing 120 and 125 seconds, with arbitrarily large gaps
- **THEN** the report SHALL show A as 1,234 seconds and B as 245 seconds

#### Scenario: Return to previous album
- **WHEN** committed entries are A, B, A
- **THEN** the report SHALL contain three rows

### Requirement: Readable local-time report
The report SHALL show aligned columns `Started at`, `Duration`, `Artist`, `Album`, and `Album ID`. Starts SHALL use local time with a UTC offset; durations SHALL use HH:MM:SS with hours above 24 supported. Artist and album SHALL come from `record`. Missing metadata SHALL retain the history row and album ID. Unicode metadata SHALL remain readable. Reporting SHALL be allowed while the app runs and SHALL show saved history only.

#### Scenario: Missing metadata and long duration
- **WHEN** a saved record's metadata is removed and its combined duration exceeds one day
- **THEN** the report SHALL retain its ID, display a metadata fallback, and format the full hours without wrapping at 24

### Requirement: Exact confirmed offline clear
`./bin/sessions-history clear` SHALL instruct users to exit normally and wait for the app to stop. It SHALL request the exact phrase `yes I hereby confirm`. Every other response, EOF, or interruption SHALL cancel deletion. Confirmed deletion SHALL remove only `sessions_log` rows in one transaction and report success only after commit. Help and README SHALL describe both commands, saved-only reporting, offline clearing, missing-database/schema behavior, sync preservation, and the absence of reconstructed historical playback.

#### Scenario: Confirmation or cancellation
- **WHEN** the exact phrase is entered
- **THEN** only committed history SHALL be cleared after commit
- **AND** a different response, surrounding whitespace, EOF, or interruption SHALL leave all tables unchanged

#### Scenario: Missing database or schema
- **WHEN** either command targets a missing database or history table
- **THEN** it SHALL report an error without creating or upgrading anything
