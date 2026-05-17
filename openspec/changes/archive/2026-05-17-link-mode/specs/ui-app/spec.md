## ADDED Requirements

### Requirement: Link mode empty state view
Link mode SHALL include an empty state grid (hidden by default) with a cover placeholder displaying "No Unlinked Records" text, using the same visual pattern as the standby "Record Not Found" placeholder.

#### Scenario: Empty state HTML structure
- **WHEN** the link mode section is rendered
- **THEN** it SHALL contain a hidden empty-state grid with a cover-placeholder and "No Unlinked Records" text

### Requirement: Link mode renders empty state when no unlinked records
The `renderLink()` function SHALL check for unlinked records. When none exist, it SHALL hide the record grid and show the empty state grid. When unlinked records exist, it SHALL show the record grid and hide the empty state.

#### Scenario: No unlinked records available
- **WHEN** `renderLink()` is called and no unlinked records exist
- **THEN** the record grid SHALL be hidden and the empty state grid SHALL be visible

#### Scenario: Unlinked records available
- **WHEN** `renderLink()` is called and unlinked records exist
- **THEN** the record grid SHALL be visible and the empty state grid SHALL be hidden

### Requirement: UI re-fetches data after sync
After sync completes (success or error), the UI SHALL re-fetch records and styli from the API to ensure all views have current data without requiring a page refresh.

#### Scenario: Sync completes successfully
- **WHEN** the sync SSE stream sends "Sync complete"
- **THEN** the UI SHALL call `fetchRecords()` and `fetchStyli()` to refresh state

#### Scenario: Sync fails
- **WHEN** the sync SSE stream sends "Sync error"
- **THEN** the UI SHALL still call `fetchRecords()` and `fetchStyli()` to refresh state
