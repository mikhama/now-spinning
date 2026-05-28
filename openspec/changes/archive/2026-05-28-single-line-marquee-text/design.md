## Context

The current frontend renders artist names, album titles, and the active track name in the record information column. On the target 4.3 inch display, longer values wrap onto multiple lines, which breaks the intended vertical rhythm and can push neighboring UI elements out of balance. During implementation, the controlling layout issue was that the metadata lane could expand to the width of its contents, which prevented overflow detection from ever activating. The existing typography hierarchy is already part of the design system, so this change needs to preserve the established fonts, sizes, and colors while introducing a predictable overflow behavior that works across Standby, Play, Link, and Re-Link.

## Goals / Non-Goals

**Goals:**
- Keep artist, album, and current track text on a single line in all record-driven views.
- Preserve full readability for long metadata by using a shared marquee-style overflow treatment instead of shrinking the type scale.
- Apply one reusable implementation pattern across the affected fields so the behavior stays consistent between modes.

**Non-Goals:**
- Redesign the overall information layout or change the existing typography hierarchy.
- Introduce backend, API, or data-model changes.
- Add manual user controls for pausing or toggling marquee behavior.

## Decisions

### 1. Use a shared marquee field structure for metadata text
Artist, album, and now-playing text will be rendered through a reusable single-line container pattern. The container provides a clipped viewport, while an inner track holds a primary copy, a fixed gap, and a duplicate copy that CSS can reuse for the looping ticker state.

Rationale: A shared structure keeps the behavior consistent across modes and avoids one-off CSS rules for each field. A simple ellipsis treatment was rejected because it preserves layout but hides the full text, which does not satisfy the readability goal.

### 2. Constrain the marquee lane to the info column
Each metadata lane must be width-constrained by the info column and explicitly allowed to shrink within the grid layout. Overflow is measured against that visible lane, not against an auto-sized content box.

Rationale: Without this constraint, the field can grow to the width of its content, which makes even extremely long values appear to "fit" and prevents the marquee state from ever turning on.

### 3. Detect overflow in the frontend after content updates
The frontend will measure whether each metadata string exceeds its available width after render and toggle an overflow state only for fields that need animation. This check should run whenever record content changes and when layout-affecting events such as resize occur.

Rationale: Always animating every metadata field would add unnecessary motion and make short labels harder to scan. A CSS-only approach cannot reliably distinguish between fitting and overflowing text in the current layout.

### 4. Let CSS own the ticker animation once overflow state is known
Overflowing metadata will remain on one line and scroll horizontally in a loop using the shared CSS marquee structure and keyframes. Frontend code should only set text content and toggle the overflow state; it should not build animation DOM on each render.

Rationale: This keeps the implementation simpler and more robust. The animation structure becomes stable in markup and styling, while JS stays focused on the one part CSS cannot do reliably by itself: deciding whether the text actually overflows.

### 5. Preserve existing typography in both static and animated states
The marquee treatment will not redefine the existing font family, font size, weight, color, or semantic role of artist, album, and track text. It only changes line breaking and overflow presentation.

Rationale: The current design system already defines the visual hierarchy. Keeping typography stable limits the scope of the change and reduces the risk of regressions in the rest of the UI.

## Risks / Trade-offs

- Motion fatigue from multiple long strings animating at once -> Only animate fields that actually overflow, and use a restrained speed with an initial pause.
- Width measurements may be wrong before fonts finish loading -> Run the overflow check after the relevant render path and after fonts are available, then recompute on resize.
- The CSS-owned ticker uses a fixed motion profile rather than a per-string computed duration -> Accept the simpler behavior unless a later change specifically requires variable speed tied to text length.
- Extra DOM structure for duplicated marquee content increases complexity slightly -> Limit the pattern to the three affected metadata field types and keep the structure shared and static in markup.

## Migration Plan

No data migration is required. Implementation should update the shared metadata markup, constrain the metadata lane in layout, add the CSS overflow treatment, and keep frontend helpers focused on text updates plus overflow detection. Then verify long-text behavior in Standby, Play, Link, and Re-Link.

## Open Questions

No unresolved design questions at this stage.