## 1. Play track label formatting

- [x] 1.1 Add a Play mode formatting helper in `ui/app.js` that derives the visible track label from the current record and current track, trimming values and detecting when the track artist is separate from the album artist.
- [x] 1.2 Update the Play render inputs so the now-playing field uses the formatted track label while preserving the existing title-only output for tracks without a separate artist.

## 2. Verification

- [x] 2.1 Verify a record with track-level artists distinct from the album artist renders `{song_title} ({artist})` in the Play now-playing field.
- [x] 2.2 Verify a record whose track artist is missing or matches the album artist still renders only `{song_title}` in the Play now-playing field.
- [x] 2.3 Verify the longer formatted now-playing label still follows the existing single-line marquee behavior when it overflows.