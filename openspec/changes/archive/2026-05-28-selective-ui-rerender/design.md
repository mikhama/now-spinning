## Context

The current frontend funnels most state changes through a single `render()` function that updates the top bar, mode visibility, action groups, and the active view's record metadata. That same path is invoked for real content changes such as record, side, track, or mode transitions, but it is also invoked for unrelated refreshes such as periodic temperature polling and post-layout recomputation. Because `setMetaText()` always clears and reapplies marquee state before measuring overflow again, unchanged long-text fields restart their ticker animation whenever those unrelated refreshes happen.

This change stays within the existing three-file frontend and current DOM structure. The goal is to preserve the current visuals while narrowing which DOM slices are allowed to update for a given event.

## Goals / Non-Goals

**Goals:**
- Preserve active marquee animation for unchanged artist, album, and track fields during unrelated UI refreshes.
- Update only the DOM slices whose source state actually changed, especially separating top-bar refreshes from record metadata refreshes.
- Keep overflow measurement accurate when text changes or layout width changes.

**Non-Goals:**
- Redesign the UI layout, typography, or marquee animation treatment.
- Introduce a framework, reactive library, or external dependency.
- Optimize every DOM write in the app beyond the visible rerender sources involved in this bug.

## Decisions

### 1. Split the current full render path into scoped UI slice updaters
The frontend will keep a single render coordinator, but it will compute which slices are dirty and call targeted updaters such as top-bar updates, mode/action visibility updates, and active-section content updates only when their inputs changed.

Rationale: This fixes the root cause without changing the overall app architecture. Replacing the whole render model with a framework or virtual DOM would be disproportionate for a small vanilla JS UI.

### 2. Make metadata updates idempotent when text is unchanged
Metadata field helpers will compare the next text value against the last rendered value and skip rewriting the marquee DOM when the content is unchanged. Overflow remeasurement will be treated as a separate concern from content assignment.

Rationale: The marquee bug exists because unchanged text is rewritten on every refresh. A content-aware helper preserves animation continuity while still allowing normal updates when the record, side, or track actually changes.

### 3. Handle layout-driven marquee checks through a dedicated remeasure path
Resize and `document.fonts.ready` events will trigger marquee remeasurement for currently visible metadata fields without forcing a full content rerender. The same targeted remeasure path can be reused when a section's text changes.

Rationale: Layout changes still need overflow detection, but they do not require resetting every visible field. A dedicated remeasure path keeps correctness without recreating the original bug.

### 4. Use conservative fallbacks for section-level changes
Mode changes, record identity changes, side changes, and track changes will still rerender the affected section because those events legitimately change the visible content. Dirty checking will stay coarse at the section or field level rather than trying to diff arbitrary DOM nodes.

Rationale: The important optimization here is avoiding unrelated rewrites, not implementing a fragile micro-diff engine. Conservative section-level updates are simpler to reason about and safer to verify.

## Risks / Trade-offs

- Dirty-state tracking can miss a dependency and leave stale DOM -> Keep the tracked inputs explicit and fall back to rerendering the affected section when any key identifier changes.
- Separating content updates from marquee measurement adds some bookkeeping -> Limit the extra state to visible UI slices and metadata fields involved in this regression.
- Layout remeasurement without full rerender may expose hidden assumptions in current helpers -> Scope the remeasure path to visible metadata fields and validate it against resize and font-ready events.

## Migration Plan

No migration or rollout sequencing is required. Implementation should introduce scoped render/update helpers in `ui/app.js`, route temperature and other unrelated updates through the narrower path, and then verify that marquee animation continuity is preserved while record, side, track, and mode changes still update correctly.

## Open Questions

No open questions at proposal time. The implementation can stay inside the existing frontend module boundaries.