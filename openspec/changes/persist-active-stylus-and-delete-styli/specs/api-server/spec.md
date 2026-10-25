## ADDED Requirements

### Requirement: Stylus responses expose saved selection
Stylus list and individual responses, including model and mock data, SHALL include a boolean `active`. Lists SHALL use stable text-ID order.

#### Scenario: List and detail agree
- **WHEN** clients request styli and an individual saved stylus
- **THEN** their boolean active flags SHALL agree with persisted selection

### Requirement: Guarded stylus activation endpoint
The server SHALL provide `POST /styli/<id>/activate`, returning JSON `{"success": true}` only after persistence, JSON 404 for a missing target, JSON 500 on persistence failure, and JSON 409 when backend playback status is `play`. The playback guard and persistence SHALL be serialized with playback transitions under the tracker's lock regardless of UI mode, debug hash, or request source.

#### Scenario: Stopped activation
- **WHEN** an existing stylus is activated while backend playback is stopped
- **THEN** the selected ID SHALL persist before success is returned

#### Scenario: Playback rejection
- **WHEN** activation is requested during backend playback
- **THEN** the server SHALL return JSON 409 without changing selection, hours, pending usage, or tracking baseline

#### Scenario: Playback start races activation
- **WHEN** activation races a playback-start transition
- **THEN** either activation SHALL commit before playback starts or activation SHALL return 409
- **AND** playback SHALL NOT start between the guard and persistence

#### Scenario: Missing or failed persistence
- **WHEN** the target is missing or persistence fails while stopped
- **THEN** the server SHALL return JSON 404 or 500 respectively without selecting a different stylus
