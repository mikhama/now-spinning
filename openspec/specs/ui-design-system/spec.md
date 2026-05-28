# ui-design-system Specification

## Purpose
Design system for the Now Spinning turntable controller UI, defining colors, typography, sizing units, and visual treatments.
## Requirements
### Requirement: Rem-based sizing units
All dimensional values (font sizes, widths, heights, padding, margins, gaps, box-shadows) SHALL use rem units. The root font-size SHALL be calculated as `calc(var(--screen-width) / 50 * var(--dpi-correction))` where `--screen-width` is the physical display width in cm (default 9.37cm) and `--dpi-correction` compensates for browser DPI assumptions (default 1). Body dimensions SHALL be `50rem × 30rem`. Border widths (1px, 2px) remain in px for crispness.

#### Scenario: Root font-size is calculated from physical dimensions
- **WHEN** the stylesheet is loaded
- **THEN** `html` SHALL compute font-size from `--screen-width / 50 * --dpi-correction`

#### Scenario: Body uses rem dimensions
- **WHEN** the UI renders
- **THEN** body width SHALL be `50rem` and height SHALL be `30rem`

#### Scenario: Uniform scaling
- **WHEN** `--screen-width` or `--dpi-correction` is changed
- **THEN** all UI elements SHALL scale proportionally (fonts, spacing, dimensions)

### Requirement: Design system color palette
The UI SHALL use CSS custom properties matching the design system palette: `--paper: #efe6d4`, `--paper-dark: #e4d9c0`, `--cream: #f5ecd8`, `--ink: #1a1410`, `--ink-soft: #3a2e24`, `--ink-mute: #6b5c4a`, `--amber: #b8612b`, `--amber-deep: #8a3f15`, `--vinyl: #0d0a08`, `--gold: #b8944a`, `--red-ink: #9a2e1f`.

#### Scenario: CSS custom properties are defined
- **WHEN** the stylesheet is loaded
- **THEN** all design system color variables SHALL be defined on `:root`

#### Scenario: Page background uses paper color
- **WHEN** the UI renders
- **THEN** the body background SHALL be `var(--paper)` (#efe6d4)

### Requirement: Design system typography — three font families
The UI SHALL use three self-hosted font families: Gloock (display headings, numbers), Fraunces (body text, album titles in italic), and DM Mono (metadata, labels, buttons — always uppercase with letter-spacing).

#### Scenario: Font-face declarations exist
- **WHEN** the stylesheet is loaded
- **THEN** @font-face rules SHALL define Gloock (400), Fraunces (normal 400-900, italic 400-700), and DM Mono (400, 500) loading from `fonts/` directory

#### Scenario: Artist names use Gloock
- **WHEN** a record is displayed
- **THEN** the artist name SHALL render in Gloock serif at 28px

#### Scenario: Album titles use Fraunces italic
- **WHEN** a record is displayed
- **THEN** the album title SHALL render in Fraunces italic at 24px with color `var(--amber-deep)`

#### Scenario: Metadata uses DM Mono uppercase
- **WHEN** the record ID or mode label is displayed
- **THEN** it SHALL render in DM Mono, uppercase, with letter-spacing of at least 0.15em

### Requirement: Paper grain texture overlay
The UI SHALL display a subtle paper grain texture using an SVG feTurbulence noise overlay covering the viewport, with `mix-blend-mode: multiply` and opacity 0.2, behind all content but above the background.

#### Scenario: Grain texture is visible
- **WHEN** the page renders
- **THEN** a fixed-position pseudo-element SHALL display fractalNoise texture at 0.2 opacity with multiply blend mode

#### Scenario: Grain does not intercept touches
- **WHEN** the user taps any button or interactive element
- **THEN** the grain overlay SHALL have `pointer-events: none` and NOT block interaction

### Requirement: Warm background gradients
The body background SHALL include two subtle radial gradients: an amber-tinted ellipse at top-left (8% opacity) and a dark-tinted ellipse at bottom-right (5% opacity).

#### Scenario: Background has warm gradients
- **WHEN** the page renders
- **THEN** the body SHALL have radial-gradient overlays creating subtle warm spots

### Requirement: Top bar vintage styling
The top bar SHALL use `background: var(--paper)`, `border-bottom: 2px solid var(--ink)`, with mode label in DM Mono 11px uppercase and stylus hours in DM Mono 11px color `var(--ink-mute)`.

#### Scenario: Top bar renders with design system styling
- **WHEN** the UI loads
- **THEN** the top bar SHALL have a paper background, 2px ink bottom border, and monospace labels

### Requirement: Cover image border treatment
Cover images SHALL have `border: 1px solid var(--ink)` and a layered box-shadow: `0 1px 0 rgba(26,20,16,0.15), 0 10px 30px rgba(26,20,16,0.25), 0 30px 50px rgba(26,20,16,0.15)`.

#### Scenario: Cover image has vintage border
- **WHEN** a record cover is displayed
- **THEN** it SHALL have a 1px ink border and warm-toned layered shadow

### Requirement: Action bar button styling
Action bar buttons SHALL use `background: var(--ink)`, `color: var(--paper)`, `border: 1px solid var(--ink-soft)`, font-family DM Mono at 14px uppercase with letter-spacing 0.15em.

#### Scenario: Buttons render with dark vintage style
- **WHEN** action buttons are displayed
- **THEN** they SHALL have dark ink background, paper-colored text, and monospace font

### Requirement: Status and error tag styling
Link status tags and error tags SHALL use DM Mono uppercase, `color: var(--amber-deep)`, `border: 1px solid var(--amber-deep)`, `background: transparent`, with letter-spacing 0.15em.

#### Scenario: Status tag uses amber accent
- **WHEN** a "Linked" or "Not Linked" status tag is displayed
- **THEN** it SHALL have amber-deep colored text and border with no background fill

#### Scenario: Error tag uses red-ink color
- **WHEN** a "Link Error" or error state is displayed
- **THEN** it SHALL have `color: var(--red-ink)` and `border-color: var(--red-ink)`

### Requirement: Now-playing track styling
The currently playing track name in Play mode SHALL use Fraunces at 20px with `color: var(--amber-deep)` and a top border of `1px solid var(--ink-soft)`.

#### Scenario: Track name renders with amber accent
- **WHEN** Play mode displays the current track
- **THEN** the track name SHALL be in Fraunces 20px with amber-deep color

### Requirement: Cover placeholder vintage styling
Error state placeholders SHALL use `background: var(--paper-dark)`, `border: 1px solid var(--ink-soft)`, with placeholder text in DM Mono uppercase, `color: var(--ink-mute)`, letter-spacing 0.15em.

#### Scenario: Placeholder matches design system
- **WHEN** an error state shows a cover placeholder
- **THEN** it SHALL use paper-dark background, ink-soft border, and DM Mono text

### Requirement: Stylus mode typography
In Stylus mode, the stylus name SHALL use Fraunces italic (same style as album title) with `color: var(--amber-deep)`, and the hours/distance SHALL use DM Mono uppercase `color: var(--ink-mute)`. The stylus section SHALL be wrapped in a `1px solid var(--amber-deep)` border with padding, forming a card.

#### Scenario: Stylus info uses design system fonts
- **WHEN** Stylus mode displays a stylus
- **THEN** the name SHALL be in Fraunces italic and hours in DM Mono metadata style

#### Scenario: Stylus mode has bordered card
- **WHEN** Stylus mode is active
- **THEN** the section SHALL have a 1px amber-deep border with padding

### Requirement: Record ID as entry number badge
The record ID SHALL display as a zero-padded number (e.g., "01") without a hash prefix, using Gloock serif font with `color: var(--amber-deep)`, `border: 1px solid var(--amber-deep)`, positioned absolutely at the top-right corner of the info column.

#### Scenario: Record ID format
- **WHEN** a record with id "1" is displayed
- **THEN** the record ID SHALL show "01" (zero-padded, no hash prefix)

#### Scenario: Record ID visual style
- **WHEN** a record ID is displayed
- **THEN** it SHALL use Gloock font with amber-deep color and amber-deep border box, positioned top-right

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

