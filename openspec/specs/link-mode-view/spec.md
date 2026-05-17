# link-mode-view Specification

## Purpose
Link mode UI showing unlinked records with prev/next navigation and empty state for NFC tag linking workflow.

## Requirements

### Requirement: Link mode shows only unlinked records
The link mode SHALL display only records where `linked` is false. The `getLinkRecord()` helper SHALL return the current record from the unlinked subset, and navigation (prev/next) SHALL cycle within unlinked records only.

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

### Requirement: Link mode empty state
When no unlinked records exist, link mode SHALL display a cover placeholder with "No Unlinked Records" text, matching the standby not-found visual pattern. The action bar SHALL show only the Mode button (same as standby fallback).

#### Scenario: No unlinked records
- **WHEN** the user enters link mode and all records have `linked: true`
- **THEN** the UI SHALL show a cover placeholder with "No Unlinked Records" text and only the Mode button in the action bar

#### Scenario: No records at all
- **WHEN** the user enters link mode and the records list is empty
- **THEN** the UI SHALL show the same empty state with "No Unlinked Records" text
