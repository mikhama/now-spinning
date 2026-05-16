## ADDED Requirements

### Requirement: Sync view displays status text
The sync view SHALL display a single status line centered within a bordered frame. The status text SHALL use the same font styling as the stylus hours display (DM Mono, monospace). The initial status text SHALL read "Step 1/3. Downloading collection updates..."

#### Scenario: User navigates to sync view
- **WHEN** user navigates to `#sync`
- **THEN** the view SHALL display a bordered frame with centered text "Step 1/3. Downloading collection updates..."

#### Scenario: Sync view frame matches stylus frame
- **WHEN** the sync view is rendered
- **THEN** the frame SHALL have the same border, padding, and sizing as the stylus mode frame

### Requirement: Sync view has correct header label
The top-left mode label SHALL display "Sync" when the sync view is active.

#### Scenario: Mode label shows Sync
- **WHEN** the sync view is active
- **THEN** the mode label in the top bar SHALL read "Sync"

### Requirement: Sync view has a Sync button
The sync view footer SHALL contain a single "Sync" button with no prev/next navigation buttons.

#### Scenario: Sync footer layout
- **WHEN** the sync view is active
- **THEN** the footer SHALL display only a "Sync" button without prev or next buttons

### Requirement: Sync view is accessible via hash routing
The sync view SHALL be accessible via the `#sync` URL hash, following the same hash routing pattern as other modes.

#### Scenario: Hash navigation to sync
- **WHEN** the URL hash is set to `#sync`
- **THEN** the app SHALL switch to the sync mode and render the sync view
