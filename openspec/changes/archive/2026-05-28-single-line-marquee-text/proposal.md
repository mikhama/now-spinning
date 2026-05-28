## Why

Artist names, album titles, and track names currently wrap when the text is longer than the available width, which breaks the intended layout on the small display and makes the information harder to scan. This should be corrected now because these fields are central to every record view and long names are common in the collection.

## What Changes

- Keep artist, album, and track text on a single line in record-driven views instead of allowing multi-line wrapping.
- Add a marquee or news-ticker style overflow treatment for long text so the full value remains readable without shrinking the entire typographic system.
- Constrain metadata lanes to the available info-column width so long values overflow against the visible viewport instead of expanding the layout.
- Use a CSS-owned marquee structure and animation, while frontend code only updates the text and decides whether overflow mode is needed.
- Apply the single-line overflow behavior consistently anywhere the UI renders record artist, album title, or current track name.
- Define the required visual behavior for resting, animated, and non-overflow states so implementation is predictable across modes.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `ui-app`: Record metadata views must keep artist, album, and current track text on one line while preserving readability for long values.
- `ui-design-system`: The typography system must define a constrained marquee lane and ticker treatment for long metadata strings on the display.

## Impact

- Affected specs: `ui-app`, `ui-design-system`
- Affected frontend code: `ui/index.html`, `ui/style.css`, `ui/app.js`
- No backend, API, or data model changes are expected