## Why

The current UI uses a generic system font (Inter/sans-serif) with Apple-inspired gray styling that doesn't match the project's identity. A design system has been created (`design.html`) defining a vintage newspaper/vinyl record catalog aesthetic with warm paper tones, serif typography (Gloock, Fraunces, DM Mono), and amber/rust accent colors. The UI needs to be restyled to use this design system across all states while preserving existing functionality and layout structure.

## What Changes

- Restyle the entire UI (all 5 modes + error states) to use the design system's color palette, typography, borders, and textures
- Replace system fonts with Gloock (headings/numbers), Fraunces (body/titles), and DM Mono (metadata/labels)
- Replace gray/white/blue color scheme with warm paper backgrounds, ink-toned text, and amber accents
- Add paper grain texture overlay to the background
- Restyle action bar buttons and status tags to match the vintage editorial aesthetic
- Restyle the top bar with design system typography and borders
- Update cover image presentation with design system border/shadow treatment
- Update error/placeholder states to use design system styling
- Convert all px-based sizes to rem units so the root font-size controls physical scale (enables setting body dimensions in cm for accurate 4.3" display preview)
- Record ID styled as "entry number" badge — Gloock font, amber-deep border box, positioned top-right of info column
- Record ID display format changed from `#1` to `01` (zero-padded, no hash prefix)
- Root font-size calculated from physical screen dimensions in cm with DPI correction factor
- Stylus mode rendered as a bordered card (amber-deep border) with Fraunces italic for stylus name
- Hide "Side" action button on error/not-found states and stylus empty state

## Capabilities

### New Capabilities
- `ui-design-system`: Visual design tokens (colors, fonts, spacing, borders) and their application across all UI states for the 800×480 Raspberry Pi display

### Modified Capabilities
- `ui-app`: Visual styling requirements are changing — typography, colors, borders, button styles, and background treatment are all being replaced while layout structure and functionality remain the same

## Impact

- `ui/style.css` — Complete restyle with new colors, fonts, borders, textures
- `ui/index.html` — Font face declarations or font link references added
- `ui/fonts/` — Self-hosted .woff2 font files already present in the project
- `ui/app.js` — Record ID formatting (zero-padded, no hash), Side button visibility logic for error/empty states
- No API or backend changes
