## Context

The Now Spinning UI is a fixed 800×480 pixel interface for a Raspberry Pi 4.3" touchscreen display. It currently uses Inter/system fonts with an Apple-inspired gray/white color scheme. A comprehensive design system has been created in `design.html` documenting a vintage newspaper/vinyl catalog aesthetic. The UI has 5 modes (Standby, Play, Link, Re-Link, Stylus), error states, and a bottom action bar — all need restyling while preserving the existing DOM structure and JavaScript logic.

Font files (.woff2) are already hosted in `ui/fonts/` — Gloock, Fraunces, and DM Mono.

## Goals / Non-Goals

**Goals:**
- Apply the design system's color palette, typography, borders, and texture to all UI states
- Maintain the existing 800×480 fixed layout and DOM structure
- Preserve all JavaScript functionality unchanged
- Ensure readability on a 4.3" physical display with touch targets

**Non-Goals:**
- Changing the DOM structure in `index.html` (beyond adding font declarations)
- Modifying `app.js` logic or behavior
- Adding responsive breakpoints (display is fixed size)
- Adding scroll-driven animations or hover interactions (touchscreen, not mouse)
- Implementing the vinyl record spinning element (purely decorative, not applicable to this UI)

## Decisions

### 1. CSS-only restyle with @font-face in style.css
**Decision**: All font-face declarations and styling go in `style.css`. No changes to `index.html` link elements.
**Rationale**: Fonts are already self-hosted in `ui/fonts/`. Keeping everything in CSS maintains the three-file constraint and avoids network requests to Google Fonts.

### 2. Simplified texture overlay
**Decision**: Use the SVG feTurbulence grain texture from the design system but at reduced opacity (0.2 instead of 0.35) for the small display.
**Rationale**: On a 4.3" display, heavy grain can reduce text legibility. The grain provides the tactile paper feel at lower intensity.

### 3. Typography scale adapted for 800×480
**Decision**: Use rem units (based on 16px equivalent) rather than clamp() since there are no breakpoints:
- Mode label / metadata: DM Mono 1.1rem, uppercase, letter-spacing 0.2em
- Record ID: Gloock 2.4rem, amber-deep, bordered badge positioned top-right
- Artist name: Gloock 3rem
- Album title: Fraunces italic 2.2rem
- Track name: Fraunces 1.8rem, ink-soft color
- Buttons: DM Mono 1.3rem, uppercase, letter-spacing 0.15em
- Stylus name: Fraunces italic 2.2rem (same style as album title)
- Stylus hours: DM Mono 1rem

**Rationale**: The design system's clamp values target a wide responsive range. At fixed 800×480, we pick specific values from within those ranges that maximize readability on the small physical display.

### 4. Button styling — ink background with paper text
**Decision**: Action bar buttons use `background: var(--ink)`, `color: var(--paper)`, `border: 1px solid var(--paper)` matching the CTA button pattern from the design system.
**Rationale**: High contrast needed for touch targets on a small display. The inverted scheme (dark bg, light text) provides clear affordance.

### 5. Cover image treatment
**Decision**: Cover images get `border: 1px solid var(--ink)` with the layered box-shadow from the design system (0 1px 0, 0 10px 30px, 0 30px 50px — all in ink rgba).
**Rationale**: Matches the album sleeve border treatment documented in the design system.

### 6. Status/error tags — amber-deep border with DM Mono
**Decision**: Status tags ("Linked", "Not Linked", "Link Error") use DM Mono uppercase, `border: 1px solid var(--amber-deep)`, `color: var(--amber-deep)`.
**Rationale**: Replaces the generic gray style with the design system's accent color for interactive status elements, matching the "connection card" pattern.

### 7. Top bar — heavy border bottom
**Decision**: Top bar uses `border-bottom: 2px solid var(--ink)`, `background: var(--paper)`, DM Mono for the mode label.
**Rationale**: Matches the masthead/section divider pattern from the design system.

### 8. Rem-based sizing with configurable root font-size
**Decision**: All px-based sizes (dimensions, font sizes, padding, gaps, margins, shadows) are converted to rem units based on a 16px baseline (1rem = 16px). The `html` element uses `font-size: calc(var(--screen-width) / 50 * var(--dpi-correction))` where `--screen-width` is the physical display width in cm and `--dpi-correction` compensates for the browser's CSS-to-physical cm mapping. Body dimensions are `50rem × 30rem`.
**Rationale**: Using rem allows the entire UI to scale uniformly by changing a single value. The calc-based approach with cm variables enables accurate physical-size previews during development — set `--screen-width: 9.37cm` and calibrate `--dpi-correction` once per dev monitor. Border widths (1px, 2px) remain in px since they should stay crisp regardless of scale.

### 9. Record ID as entry number badge
**Decision**: Record ID is displayed as a zero-padded number (e.g., "01" instead of "#1") using Gloock serif in a bordered amber-deep badge, positioned absolutely at the top-right corner of the info column.
**Rationale**: Matches the "entry number" visual pattern from the design system (`design.html`), providing a strong visual anchor for record identification. The zero-padded format without hash is cleaner and more consistent with the vintage catalog aesthetic.

### 10. Stylus mode as bordered card
**Decision**: The stylus mode section (`#mode-stylus`) is wrapped in a `1px solid var(--amber-deep)` border with padding, forming a card. Stylus name uses Fraunces italic (same as album title), matching the visual weight of album information across modes.
**Rationale**: Creates visual consistency — stylus info is presented with the same level of care as record info, using the design system's signature border treatment.

### 11. Hide irrelevant action buttons in error/empty states
**Decision**: The "Side" button is hidden (visibility: hidden) when displaying error states (NFC error, not found) in standby mode and when stylus mode shows "No styli found". Logic added to `app.js`.
**Rationale**: The Side button has no function when there's no record loaded or no styli available. Hiding it reduces confusion on the touchscreen interface.

## Risks / Trade-offs

- **[Readability at small size]** → Mitigated by using rem values derived from tested pixel sizes; minimum is 0.6875rem (11px at base 16)
- **[Grain texture performance on Pi]** → Mitigated by using CSS-rendered SVG (no image file) and reduced opacity; can be disabled via `prefers-reduced-motion` if needed
- **[Font file size]** → Mitigated by fonts already being local .woff2 files (no network dependency), and only latin subset needed
- **[Touch target sizes unchanged]** → Action bar buttons still fill their grid cells (full width/height), maintaining the same touch area
- **[Rem rounding]** → Sub-pixel rounding on some sizes is negligible at target display resolution (800×480)
