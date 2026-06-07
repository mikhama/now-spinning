## MODIFIED Requirements

### Requirement: Link mode shows only unlinked records
The link mode SHALL display only records where `linked` is false, except that a record that just completed link success MAY remain visible until the user navigates away from it. The `getLinkRecord()` helper SHALL return the current record from the unlinked subset, and navigation (prev/next) SHALL cycle within unlinked records only. After a successful link and one Prev or Next navigation action, the linked record SHALL no longer be reachable in link mode.

#### Scenario: All records are unlinked
- **WHEN** the user enters link mode and all 5 records have `linked: false`
- **THEN** the link mode SHALL show the first unlinked record and allow navigating through all 5

#### Scenario: Some records are linked
- **WHEN** the user enters link mode with 3 of 5 records having `linked: true`
- **THEN** the link mode SHALL show only the 2 unlinked records with prev/next navigation

#### Scenario: Navigate to previous unlinked record
- **WHEN** the user presses the Prev button in link mode
- **THEN** the UI SHALL display the previous record in the unlinked records list, wrapping to the last if at the beginning

#### Scenario: Navigate to next unlinked record
- **WHEN** the user presses the Next button in link mode
- **THEN** the UI SHALL display the next record in the unlinked records list, wrapping to the first if at the end

#### Scenario: Linked record disappears after navigation
- **WHEN** the current link-mode record receives a successful link result
- **AND** the user presses Next and then Prev
- **THEN** the successfully linked record SHALL NOT be shown in link mode
- **AND** the UI SHALL show the previous or next remaining unlinked record, or the empty state if none remain

### Requirement: Link mode empty state
When no unlinked records exist, link mode SHALL display a cover placeholder with "No unlinked records" text, matching the standby not-found visual pattern. The action bar SHALL show only the Mode button, same as the standby fallback.

#### Scenario: No unlinked records
- **WHEN** the user enters link mode and all records have `linked: true`
- **THEN** the UI SHALL show a cover placeholder with "No unlinked records" text and only the Mode button in the action bar

#### Scenario: No records at all
- **WHEN** the user enters link mode and the records list is empty
- **THEN** the UI SHALL show the same empty state with "No unlinked records" text

## ADDED Requirements

### Requirement: Link action waits for tag result
When the user clicks the Link button with a link-mode or re-link-mode record selected, the UI SHALL enter a pending link state for that record and SHALL render the same blinking dot indicator used by sync mode under the linked status label while it waits for a link result event.

#### Scenario: Link button starts pending state
- **WHEN** the user selects an unlinked record in link mode and clicks Link
- **THEN** the selected record SHALL remain visible
- **AND** the status area SHALL show the selected record's not-linked label
- **AND** a blinking dot indicator SHALL render under that label

#### Scenario: Re-Link button starts pending state
- **WHEN** the user selects a linked record in re-link mode and clicks Re-Link
- **THEN** the selected record SHALL remain visible
- **AND** the status area SHALL show the selected record's linked label
- **AND** a blinking dot indicator SHALL render under that label

### Requirement: Link result events update link and re-link views
The UI SHALL handle boardless link result events. A `link_success` event with a matching `record_id` SHALL clear pending state, clear link error state, and mark that record as linked in client state. A `link_error` event SHALL clear pending state and show the link error state in the current link or re-link mode.

#### Scenario: Link success in link mode
- **WHEN** the mode is link, record "1" is selected, and a pending link exists for record "1"
- **AND** a `link_success` event arrives with `{"record_id":"1"}`
- **THEN** pending state SHALL be cleared
- **AND** record "1" SHALL be marked `linked: true` in client state
- **AND** the link error state SHALL be cleared

#### Scenario: Link error in link mode
- **WHEN** the mode is link and a pending link exists
- **AND** a `link_error` event arrives
- **THEN** pending state SHALL be cleared
- **AND** the UI SHALL render the Link Error state

#### Scenario: Link success in re-link mode remains visible
- **WHEN** the mode is re-link, record "1" is selected, and a pending re-link exists for record "1"
- **AND** a `link_success` event arrives with `{"record_id":"1"}`
- **THEN** record "1" SHALL remain visible in re-link mode
- **AND** pending state SHALL be cleared

### Requirement: Re-link mode shows only linked records
The re-link mode SHALL display only records where `linked` is true. Re-link navigation SHALL cycle within linked records only, and records that receive successful re-link results SHALL remain reachable because they stay linked.

#### Scenario: Re-link shows linked records
- **WHEN** the user enters re-link mode with 2 linked records and 3 unlinked records
- **THEN** re-link mode SHALL show only the 2 linked records

#### Scenario: Re-link navigation wraps within linked records
- **WHEN** the user presses Prev or Next in re-link mode
- **THEN** the UI SHALL display the previous or next record in the linked records list, wrapping at boundaries

#### Scenario: Re-link success remains in linked list
- **WHEN** a visible re-link-mode record receives a successful link result
- **AND** the user presses Next and then Prev
- **THEN** the successfully re-linked record SHALL still be reachable in re-link mode

### Requirement: Re-link mode empty state
When no linked records exist, re-link mode SHALL display a cover placeholder with "No linked records" text, matching the standby not-found visual pattern. The action bar SHALL show only the Mode button, same as the standby fallback.

#### Scenario: No linked records
- **WHEN** the user enters re-link mode and all records have `linked: false`
- **THEN** the UI SHALL show a cover placeholder with "No linked records" text and only the Mode button in the action bar

#### Scenario: No records at all
- **WHEN** the user enters re-link mode and the records list is empty
- **THEN** the UI SHALL show the same empty state with "No linked records" text
