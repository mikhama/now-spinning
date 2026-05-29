## MODIFIED Requirements

### Requirement: Play/stop status events
When a `status` event with `status: "play"` is received, the UI SHALL transition to play mode without synthesizing a fallback record. When `status: "stop"` is received, the UI SHALL transition to standby mode while preserving the current record or standby error context.

#### Scenario: Status play event with active record
- **WHEN** a `status` event is received with `{"status": "play"}` and `currentRecordId` points to an existing record
- **THEN** the mode SHALL change to `"play"`
- **AND** `currentRecordId` SHALL remain set to that record

#### Scenario: Status play event without active record
- **WHEN** a `status` event is received with `{"status": "play"}` and no current record is active because the latest scan resolved to record-not-found
- **THEN** the mode SHALL change to `"play"`
- **AND** `currentRecordId` SHALL remain `null`
- **AND** the event handling SHALL NOT assign a default or fallback record

#### Scenario: Status stop event preserves fallback context
- **WHEN** a `status` event is received with `{"status": "stop"}` after play mode was entered without a valid current record
- **THEN** the mode SHALL change to `"standby"`
- **AND** `currentRecordId` SHALL remain `null`
- **AND** `standbyError` SHALL remain `"not-found"`