## Context

The Now Spinning UI is a single-page app (800×480 viewport) with hash-based routing between modes: standby, play, link, re-link, and stylus. Each mode has a `<section>` in `index.html`, an action group in the footer, and a render function in `app.js`. The stylus mode uses a bordered frame with a name, capacity bar, and hours display. We need to add a sync view that reuses this frame layout but replaces the content with a centered status line.

## Goals / Non-Goals

**Goals:**
- Add a sync view accessible at `#sync` that follows existing mode patterns
- Reuse the stylus frame visual style (bordered box) for layout consistency
- Show a single centered status text line using the same font as the stylus hours display (`DM Mono`)
- Provide a "Sync" button in the footer (no prev/next navigation)
- Display "Sync" as the mode label in the top-left corner

**Non-Goals:**
- Actual sync/download functionality (backend integration is future work)
- Multi-step progress transitions (only the initial static status text for now)
- WebSocket events for sync status updates

## Decisions

1. **Follow existing mode pattern** — Add sync as a new entry in `MODES` array, with its own section, action group, and render function. This is consistent with how all other modes are implemented.

2. **Reuse stylus frame CSS** — The sync view section uses the same border/padding/sizing as `#mode-stylus`. Rather than duplicating styles, apply a shared class or reuse the same CSS properties via a grouped selector.

3. **Status text styling** — Use `DM Mono` monospace font at the same size as `.stylus-distance` (1.4rem) to match the user's request for "the same font as for number of hours of cartridge." Center it vertically and horizontally within the frame using flexbox.

4. **No prev/next buttons** — The sync action group has only a "Sync" button centered in the footer, with placeholder divs for spacing consistency.

## Risks / Trade-offs

- **Static status text only** — The status line is hardcoded for now. When real sync is implemented, the render function will need to read from state. This is acceptable as a scaffold.
- **MODES array ordering** — Sync is appended after stylus. The Mode button cycles through all modes including sync, which means users can navigate to it manually. This is fine for dev/demo purposes.
