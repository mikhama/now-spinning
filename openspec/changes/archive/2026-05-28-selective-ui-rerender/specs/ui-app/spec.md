## ADDED Requirements

### Requirement: Scoped UI updates for unrelated state changes
The frontend SHALL update only the DOM slices affected by a state change instead of rerunning the full visible view render for every event. Updates that only change top-bar or stylus summary data SHALL NOT rewrite record metadata fields when the visible record, side, and track content are unchanged.

#### Scenario: Temperature refresh updates only top-bar data
- **WHEN** periodic temperature polling returns a new reading while the current mode and visible record metadata are unchanged
- **THEN** the UI SHALL update the temperature display without rewriting the active artist, album, or track metadata DOM

#### Scenario: Stylus-hours update leaves record metadata untouched
- **WHEN** a stylus-hours event is received while a record view is visible and the visible record, side, and track content are unchanged
- **THEN** the UI SHALL update only the stylus-related display elements and SHALL preserve the existing record metadata DOM

### Requirement: Marquee continuity across non-content refreshes
The frontend SHALL preserve active marquee animation state for artist, album, and track fields across updates that do not change the field text or visible lane width. Overflow measurement SHALL rerun when metadata text changes or when a layout-affecting event requires remeasurement.

#### Scenario: Unchanged marquee survives periodic refresh
- **WHEN** a long artist, album, or track field is already animating and an unrelated refresh occurs
- **THEN** the marquee SHALL continue without restarting because the field text was not rewritten

#### Scenario: Metadata change recomputes marquee state
- **WHEN** the visible record, side, or track changes
- **THEN** the affected metadata field SHALL update its text and SHALL recompute whether marquee overflow is required

#### Scenario: Layout change remeasures overflow
- **WHEN** fonts finish loading or the window is resized
- **THEN** the visible marquee fields SHALL remeasure overflow against the current lane width and SHALL keep or clear animation according to the new fit