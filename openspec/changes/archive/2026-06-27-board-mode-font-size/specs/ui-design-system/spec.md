## MODIFIED Requirements

### Requirement: Rem-based sizing units
All dimensional values (font sizes, widths, heights, padding, margins, gaps, box-shadows) SHALL use rem units. In boardless mode only, the root font-size SHALL be calculated as `calc(var(--screen-width) / 50 * var(--dpi-correction))` where `--screen-width` is the physical display width in cm (default 9.37cm) and `--dpi-correction` compensates for browser DPI assumptions (default 1). In normal board mode, the UI SHALL NOT set `font-size` on the `<html>` element. Body dimensions SHALL be `50rem × 30rem`. Border widths (1px, 2px) remain in px for crispness.

#### Scenario: Boardless root font-size is calculated from physical dimensions
- **WHEN** the stylesheet is loaded and the `<html>` element is marked as boardless mode
- **THEN** `html` SHALL compute font-size from `--screen-width / 50 * --dpi-correction`

#### Scenario: Normal board root font-size is not set
- **WHEN** the stylesheet is loaded and the `<html>` element is not marked as boardless mode
- **THEN** the UI stylesheet SHALL NOT set `font-size` on `html`

#### Scenario: Body uses rem dimensions
- **WHEN** the UI renders
- **THEN** body width SHALL be `50rem` and height SHALL be `30rem`

#### Scenario: Uniform scaling in boardless mode
- **WHEN** the `<html>` element is marked as boardless mode and `--screen-width` or `--dpi-correction` is changed
- **THEN** all rem-sized UI elements SHALL scale proportionally (fonts, spacing, dimensions)
