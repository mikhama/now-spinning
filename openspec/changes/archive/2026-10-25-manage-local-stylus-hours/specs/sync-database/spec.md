## ADDED Requirements

### Requirement: Database sets absolute stylus hours
The database layer SHALL provide a shared operation for replacing an existing stylus's `distance_hours` with a finite, nonnegative absolute total. It SHALL use an existing database and a single transaction for reading the previous total and saving the replacement, report the previous and new totals after commit, and report a missing row without creating it. Invalid values or save failures SHALL leave totals unchanged.

#### Scenario: Set replaces rather than increments
- **WHEN** stylus `1` has `102.4` hours and the operation sets `97.3` hours
- **THEN** the committed total SHALL equal `97.3`
- **AND** the operation SHALL report `102.4` as the previous total and `97.3` as the new total

#### Scenario: Reject invalid values
- **WHEN** the operation receives a negative or non-finite value
- **THEN** it SHALL reject the request and leave all saved totals unchanged

#### Scenario: Missing row
- **WHEN** the operation targets a missing stylus
- **THEN** it SHALL report no updated row and leave existing rows unchanged

### Requirement: Collection sync preserves local stylus hours
Collection sync SHALL ignore `distance_hours` from `my-musical-journey` regardless of whether the field remains present. New stylus rows SHALL start at zero hours. Existing rows SHALL retain their local total, including totals previously imported, accrued through playback, or set/reset locally.

#### Scenario: New stylus with legacy remote hours
- **WHEN** sync imports a new stylus whose remote `distance_hours` is `97.3`
- **THEN** its local total SHALL start at zero

#### Scenario: New stylus without remote hours
- **WHEN** sync imports a new stylus without `distance_hours`
- **THEN** its local total SHALL start at zero

#### Scenario: Existing local totals survive sync
- **WHEN** an existing stylus is synced with a different remote total or with the field removed
- **THEN** its local total SHALL remain unchanged

## MODIFIED Requirements

### Requirement: Database resets stylus hours
The database layer SHALL provide an operation that resets an existing stylus row by setting `distance_hours` to `0`, delegating to the shared absolute-total operation while retaining its boolean updated-row result.

#### Scenario: Reset existing stylus hours
- **WHEN** the reset operation is called for an existing stylus ID
- **THEN** the database SHALL update that stylus row with `distance_hours` equal to `0`
- **AND** the operation SHALL report that a row was updated

#### Scenario: Reset missing stylus hours
- **WHEN** the reset operation is called for a stylus ID that does not exist
- **THEN** the database SHALL leave existing rows unchanged
- **AND** the operation SHALL report that no row was updated
