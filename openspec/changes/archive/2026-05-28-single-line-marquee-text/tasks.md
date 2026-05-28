## 1. Shared marquee structure

- [x] 1.1 Update the record metadata markup so artist, album, and play-track fields use a shared single-line marquee container structure.
- [x] 1.2 Add reusable CSS classes for single-line clipping, static text state, and looping ticker animation while preserving the existing typography styles.

## 2. Overflow detection and rendering

- [x] 2.1 Add a frontend helper that sets metadata text content and measures whether each field overflows after render.
- [x] 2.2 Apply the overflow helper in Standby, Play, Link, and Re-Link render paths so artist, album, and current track fields switch between static and marquee states as content changes.
- [x] 2.3 Recompute overflow state after layout-affecting events such as initial font-ready render or window resize.

## 3. Verification

- [x] 3.1 Verify that short artist, album, and track values stay on one line without animation in all affected modes.
- [x] 3.2 Verify that long artist, album, and track values stay on one line and loop with the ticker treatment in all affected modes.
- [x] 3.3 Confirm the marquee treatment preserves the existing font families, sizes, colors, and surrounding layout spacing.