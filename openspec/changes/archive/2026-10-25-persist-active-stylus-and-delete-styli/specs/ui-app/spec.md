## ADDED Requirements

### Requirement: Persisted stylus navigation
The UI SHALL initialize Stylus mode from the saved active flag and navigate in stable text-ID order. Prev/Next SHALL persist the adjacent stylus with wraparound through the activation endpoint and update selection and both wear bars only after confirmed success.

#### Scenario: Saved selection loads
- **WHEN** the application loads with a saved active stylus other than the first ID
- **THEN** Stylus mode and the compact wear bar SHALL use that saved stylus

#### Scenario: Navigation wraps and persists
- **WHEN** Next is pressed at the last ID or Prev at the first ID while stopped
- **THEN** the UI SHALL activate the first or last ID respectively
- **AND** both wear bars SHALL display the newly selected stylus's hours and capacities after success

### Requirement: Stylus navigation guards and recovery
The UI SHALL track received backend playback status independently of the displayed mode and debug hash. Prev/Next SHALL be disabled while that status is `play` or activation is pending. Reset SHALL be disabled while activation is pending. Failures SHALL replace stylus details with the accessible message `An error occurred!`, using the existing empty-state presentation. Reset SHALL be hidden in this error state. Prev/Next SHALL remain available while stopped to retry; there SHALL be no separate banner or Retry button. An unconfirmed network outcome SHALL trigger a refresh of saved selection; retry navigation SHALL refresh any still-uncertain selection before choosing and persisting the adjacent ID.

#### Scenario: Playback across modes and hashes
- **WHEN** the backend reports `play` while any mode or debug hash is displayed
- **THEN** stylus navigation SHALL remain disabled until a non-playing status is received

#### Scenario: Pending activation
- **WHEN** an activation request has not settled
- **THEN** repeated navigation and Reset SHALL NOT send another mutation

#### Scenario: Rejected activation
- **WHEN** activation returns 404, 409, or 500
- **THEN** the UI SHALL retain the confirmed selection and replace stylus details with the generic error state
- **AND** another Prev/Next click while stopped SHALL retry navigation and restore stylus details after success

#### Scenario: Response is lost after commit
- **WHEN** activation cannot be confirmed because of a network or response error
- **THEN** the UI SHALL reload saved selection and update the compact bar while showing the generic error state
- **AND** after failed recovery, Prev/Next SHALL reload saved selection before navigating in the chosen direction
- **AND** playback starting during recovery SHALL prevent a following activation
