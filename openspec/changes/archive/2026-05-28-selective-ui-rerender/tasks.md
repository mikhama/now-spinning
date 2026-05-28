## 1. Scoped render coordination

- [x] 1.1 Refactor `ui/app.js` so top-bar updates, mode/action visibility, and active-section content can be updated through separate helpers instead of a single unconditional full render path.
- [x] 1.2 Track the last rendered inputs needed to decide whether a change affects the top bar, the visible section, or both.
- [x] 1.3 Route temperature polling and other unrelated refreshes through the narrowest valid updater while keeping full section rerenders for mode, record, side, and track changes.

## 2. Metadata marquee preservation

- [x] 2.1 Update the metadata text helper so unchanged artist, album, and track values do not rewrite marquee DOM or restart animation.
- [x] 2.2 Add a dedicated marquee remeasure path that recalculates overflow only when metadata changes or when layout width may have changed.
- [x] 2.3 Wire resize and font-ready handling to the marquee remeasure path without forcing a full content rerender.

## 3. Verification

- [x] 3.1 Verify that periodic temperature refreshes and stylus-hours updates do not restart active marquee animation when visible metadata is unchanged.
- [x] 3.2 Verify that record, side, track, and mode changes still update the correct content and recompute marquee overflow when needed.
- [x] 3.3 Verify that resize and post-font-load remeasurement keep short text static and long text animating in the active record views.