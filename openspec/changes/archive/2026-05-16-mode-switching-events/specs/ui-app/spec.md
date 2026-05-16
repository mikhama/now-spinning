## MODIFIED Requirements

### Requirement: Five application modes
The UI SHALL support six modes: Standby, Play, Link, Re-Link, Stylus, and Sync. Mode switching via the Mode button SHALL cycle through: standby → sync → link → re-link → stylus → standby. Play mode SHALL only be reachable via WebSocket `status` events. Hash-based dev routing SHALL remain functional.

#### Scenario: Modes exist
- **WHEN** the UI is initialized
- **THEN** the mode list SHALL contain "standby", "play", "link", "re-link", "stylus", and "sync"

#### Scenario: Mode button cycles defined order
- **WHEN** the mode button is pressed in standby mode
- **THEN** the mode SHALL advance to "sync", then "link", "re-link", "stylus", and back to "standby"

#### Scenario: Play mode not in button cycle
- **WHEN** the mode button is pressed
- **THEN** "play" mode SHALL never be entered via the mode button
