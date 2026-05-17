## MODIFIED Requirements

### Requirement: Sync view displays status text
The sync view SHALL display a single status line centered within a bordered frame. The status text SHALL use the same font styling as the stylus hours display (DM Mono, monospace). The initial status text SHALL show the last sync date in format "Last updated YYYY/MM/DD" or "Last updated never" if no sync has been performed.

#### Scenario: User navigates to sync view with no previous sync
- **WHEN** user navigates to `#sync` and no sync has been performed
- **THEN** the view SHALL display "Last updated never"

#### Scenario: User navigates to sync view with previous sync
- **WHEN** user navigates to `#sync` and a previous sync was performed
- **THEN** the view SHALL display "Last updated YYYY/MM/DD" with the date of the last successful sync

#### Scenario: Sync button triggers sync and shows step statuses
- **WHEN** the user clicks the "Sync" button
- **THEN** the status text SHALL update in sequence: "Downloading collection", then "Updating database", then "Sync complete" or "Sync error"
- **AND** a blinking dot indicator SHALL appear before the status text while sync is in progress
- **AND** the blinking dot SHALL be removed when the status reaches "Sync complete" or "Sync error"

#### Scenario: Only one status line shown at a time
- **WHEN** the sync is in progress
- **THEN** the view SHALL display only the current step status — always one line on the screen

### Requirement: Sync view has a Sync button
The sync view footer SHALL contain a single "Sync" button with no prev/next navigation buttons.

#### Scenario: Sync footer layout
- **WHEN** the sync view is active
- **THEN** the footer SHALL display only a "Sync" button without prev or next buttons

#### Scenario: Sync button triggers POST /sync
- **WHEN** the user clicks the "Sync" button
- **THEN** the UI SHALL send a `POST /sync` request and consume the SSE stream to update the status text in real-time
