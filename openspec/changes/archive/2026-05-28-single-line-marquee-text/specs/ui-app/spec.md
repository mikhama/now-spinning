## ADDED Requirements

### Requirement: Single-line record metadata display
Artist names, album titles, and the current track name SHALL remain on a single line anywhere the UI renders record metadata in Standby, Play, Link, or Re-Link mode. The metadata lane SHALL stay constrained to the visible info-column width. When a value exceeds that available width, the UI SHALL preserve the single-line layout and use the approved overflow treatment instead of wrapping onto a second line.

#### Scenario: Metadata fits within the available width
- **WHEN** an artist name, album title, or current track name fits within its container
- **THEN** the text SHALL remain on one line and render without overflow animation

#### Scenario: Metadata overflows in a record view
- **WHEN** an artist name, album title, or current track name is longer than the available width in Standby, Play, Link, or Re-Link mode
- **THEN** the text SHALL remain on one line and use the overflow treatment rather than wrapping onto multiple lines

#### Scenario: Overflow state updates with new content
- **WHEN** the displayed record, side, or track changes
- **THEN** the UI SHALL recalculate whether each affected metadata field needs the overflow treatment for the newly rendered text

#### Scenario: Overflow state updates after layout changes
- **WHEN** fonts finish loading or the viewport layout changes in a way that affects the metadata lane width
- **THEN** the UI SHALL recalculate whether each affected metadata field needs the overflow treatment for the current text