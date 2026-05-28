## ADDED Requirements

### Requirement: Marquee overflow treatment for record metadata
The design system SHALL provide a reusable marquee-style overflow treatment for record metadata text. Overflowing artist, album, and track strings SHALL render inside a single-line clipped viewport that is constrained to the available lane width, preserve their existing typography, and animate horizontally in a looping ticker presentation only when the text exceeds the available width.

#### Scenario: Static presentation for non-overflowing text
- **WHEN** a metadata string fits within the available width
- **THEN** the marquee treatment SHALL render the text fully on one line without horizontal animation

#### Scenario: Ticker presentation for overflowing text
- **WHEN** a metadata string exceeds the available width
- **THEN** the marquee treatment SHALL keep the text on one line, clip it to the field width, and animate it horizontally with a looping ticker-style motion after an initial pause

#### Scenario: Shared ticker structure is reusable
- **WHEN** the marquee treatment is applied to artist, album, or track text
- **THEN** it SHALL use the shared clipped lane and ticker-track pattern defined by the design system rather than per-view bespoke overflow markup or animation behavior

#### Scenario: Existing typography is preserved
- **WHEN** the marquee treatment is applied to artist, album, or track text
- **THEN** the field SHALL keep the font family, size, weight, style, and color already defined for that metadata role