## MODIFIED Requirements

### Requirement: Five application modes
The UI SHALL support six modes: Standby, Play, Link, Re-Link, Stylus, and Sync. Mode switching via the Mode button is disabled — modes are only reachable via URL hash in dev mode or via WebSocket events (play/idle status).

#### Scenario: Modes exist
- **WHEN** the UI is initialized
- **THEN** the mode list SHALL contain "standby", "play", "link", "re-link", "stylus", and "sync"
