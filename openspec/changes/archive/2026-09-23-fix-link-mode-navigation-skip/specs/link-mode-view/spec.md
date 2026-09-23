## MODIFIED Requirements

### Requirement: Link mode shows only unlinked records
The link mode SHALL display only records where `linked` is false, except that a record that just completed link success MAY remain visible until the user navigates away from it. The `getLinkRecord()` helper SHALL return the current record from the unlinked subset, and navigation (Prev/Next) SHALL cycle within unlinked records only. When navigation dismisses a successfully linked record that was temporarily retained, Next SHALL show the immediately following remaining unlinked record in browsing order and Prev SHALL show the immediately preceding remaining unlinked record, with normal boundary wrapping. After that navigation action, the linked record SHALL no longer be reachable in link mode. If no unlinked records remain, the navigation action SHALL show the link-mode empty state.

#### Scenario: All records are unlinked
- **WHEN** the user enters link mode and all 5 records have `linked: false`
- **THEN** the link mode SHALL show the first unlinked record and allow navigating through all 5

#### Scenario: Some records are linked
- **WHEN** the user enters link mode with 3 of 5 records having `linked: true`
- **THEN** the link mode SHALL show only the 2 unlinked records with Prev/Next navigation

#### Scenario: Navigate to previous unlinked record
- **WHEN** the user presses the Prev button in link mode without a successfully linked record retained on screen
- **THEN** the UI SHALL display the previous record in the unlinked records list, wrapping to the last if at the beginning

#### Scenario: Navigate to next unlinked record
- **WHEN** the user presses the Next button in link mode without a successfully linked record retained on screen
- **THEN** the UI SHALL display the next record in the unlinked records list, wrapping to the first if at the end

#### Scenario: Next after link success selects the adjacent record
- **WHEN** records 1 through 5 are unlinked and record 2 is selected in link mode
- **AND** record 2 receives a successful link result and remains temporarily visible
- **AND** the user presses Next
- **THEN** the UI SHALL display record 3
- **AND** record 2 SHALL no longer be reachable in link mode

#### Scenario: Previous after link success selects the adjacent record
- **WHEN** records 1 through 5 are unlinked and record 4 is selected in link mode
- **AND** record 4 receives a successful link result and remains temporarily visible
- **AND** the user presses Prev
- **THEN** the UI SHALL display record 3
- **AND** record 4 SHALL no longer be reachable in link mode

#### Scenario: Next after linking the last record wraps
- **WHEN** the last unlinked record in browsing order receives a successful link result and remains temporarily visible
- **AND** at least one other unlinked record remains
- **AND** the user presses Next
- **THEN** the UI SHALL display the first remaining unlinked record

#### Scenario: Navigation after linking the only record shows empty state
- **WHEN** the only unlinked record receives a successful link result and remains temporarily visible
- **AND** the user presses Prev or Next
- **THEN** the UI SHALL show the link-mode empty state
