## Context

The synced collection and API model already allow each track to carry its own optional `artist`, but the Play mode render path only reads `track.title`. That means compilations, soundtrack records, and featured tracks lose the track-level performer information even though the data is already present in the frontend payload.

This change is limited to the Play mode metadata formatting path in `ui/app.js`. The existing marquee layout, API schema, database record shape, and sync pipeline can remain unchanged if the display string is derived at render time.

## Goals / Non-Goals

**Goals:**
- Show `{song_title} ({artist})` in Play mode when the current track provides its own artist that is meaningfully separate from the album artist.
- Preserve the existing title-only output when no separate track artist exists.
- Keep the change local to frontend rendering so current APIs and stored data remain compatible.

**Non-Goals:**
- Redesign the play metadata lane or marquee behavior.
- Change how track artist data is stored or synced.
- Add separate artist treatment to standby, link, or re-link modes, which do not show now-playing track text.

## Decisions

### Derive a display label in the Play render path
The frontend should compute a dedicated now-playing label from the current record and current track instead of changing the underlying payload shape. A small helper can return either `track.title` or `{track.title} ({track.artist})` and feed that value into the existing marquee text update flow.

Alternative considered: mutate track objects during fetch or normalization so `title` already contains the display suffix. Rejected because it mixes presentation into the data model and would make later reuse of raw track titles harder.

### Treat "separate artist" as non-empty and distinct from the album artist
The artist suffix in parentheses should appear only when the track-level artist is present after trimming whitespace and does not match the record-level artist after the same normalization. That keeps soundtrack and guest-track cases informative without producing redundant labels for albums where every track artist repeats the album artist.

Alternative considered: prepend the track artist whenever `track.artist` is non-empty. Rejected because some data sources may repeat the album artist per track, which would unnecessarily lengthen normal now-playing labels.

### Reuse the existing marquee lane unchanged
The helper should only change the text content supplied to the Play mode track field. Overflow measurement and marquee activation should continue to operate on the final rendered string, which naturally covers longer `{song_title} ({artist})` values.

Alternative considered: add a second visual field for track artist. Rejected because it would require a broader layout change and is not needed to satisfy the requested behavior.

## Risks / Trade-offs

- [Risk] Appending the track artist in parentheses produces longer strings and will trigger marquee animation more often. -> Mitigation: keep the existing single-line marquee behavior and measure overflow against the final formatted label.
- [Risk] Data may include inconsistent whitespace around track artists. -> Mitigation: normalize whitespace for comparison and for the rendered suffix before building the display string.
- [Risk] The meaning of "separate artist" could be interpreted as any populated artist field rather than one distinct from the album artist. -> Mitigation: encode the distinct-from-album rule in the spec scenarios so implementation and review use the same contract.