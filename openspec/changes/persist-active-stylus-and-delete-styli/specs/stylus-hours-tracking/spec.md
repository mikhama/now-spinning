## ADDED Requirements

### Requirement: Stopped selection switches usage tracking safely
Before changing the active stylus while stopped, the tracker SHALL persist any remaining pending usage for the previous stylus and abort selection if that save fails. After selection commits it SHALL load the new stylus's saved hours and clear the playback baseline. Selecting the already-active stylus while stopped SHALL be a no-op. Playback rejection SHALL leave all tracking state unchanged. Usage events SHALL retain the existing `stylus_hours` format.

#### Scenario: Pending usage follows the previous stylus
- **WHEN** a stopped tracker has pending seconds and another stylus is activated
- **THEN** pending seconds SHALL be saved to the previous stylus before selection commits
- **AND** subsequent playback SHALL accrue only to the new stylus

#### Scenario: Pending save fails
- **WHEN** previous pending hours cannot be saved
- **THEN** activation SHALL fail with selection, pending seconds, and current hours retained

#### Scenario: Repeated activation
- **WHEN** the saved active stylus is activated again while stopped
- **THEN** selection and tracking state SHALL remain unchanged without a selection write

#### Scenario: New tracker after restart
- **WHEN** the application restarts after committing a selection
- **THEN** subsequent playback SHALL load and accrue only to that saved stylus
