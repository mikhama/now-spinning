## Context

The UI is a fixed 800×480, three-file browser app. `setMode` owns mode transitions, `render` updates the Play view, WebSocket `status` messages provide elapsed playback time, and track selection already resolves a current side and track. Album covers are served from the same origin. The approved preview established the visual layout. A cover experiment showed that a single RGB bucket can miss a prominent color when its shades are spread across buckets, so the palette selection uses a hue family from the same 64×64 canvas sample.

## Goals / Non-Goals

**Goals:**

- Make the screensaver a Play-only overlay that starts after 10 seconds of Play and 10 seconds without touch, dismisses on the next touch, and can appear again after another 10 seconds.
- Keep artist, track title, side, album, and elapsed time current while the overlay is visible.
- Calculate a cover-specific background and contrasting black or white text automatically for every record.
- Preserve the preview's centered typography, corner alignment, and scrolling long text.

**Non-Goals:**

- Change playback detection, record data, or the normal Play controls.
- Add a new dependency or persist color data in the database.

## Decisions

### Playback and touch timing

Store the time when the UI enters Play and the last pointer interaction during Play. Schedule one timeout for the later of those timestamps plus 10 seconds. Entering another mode clears the timeout and hides the overlay. A pointer interaction dismisses the overlay and schedules the next 10-second idle deadline. This keeps UI inactivity separate from the backend's status update cadence; relying on status messages alone would continually reset an idle timer.

### Display data

Read the active record, side, and track from existing state when the overlay opens or Play data changes. Use `track.artist` when it has non-whitespace text; otherwise use `record.artist`. Show `track.title` alone on the song line, even when the normal Play view appends a track artist to its track label. Use server playback time when present; while it is unavailable or between updates, advance an elapsed display from the latest known time and wall clock.

### Cover palette

Load the current same-origin cover into a 64×64 canvas and ignore pixels with alpha below 200. Convert each remaining RGB pixel to HSV. Eligible colorful pixels have saturation at least 0.28 and value at least 0.30. Score hue centers from 0° through 355° in 5° steps: each eligible pixel contributes its saturation multiplied by `max(0, 1 - circular hue distance / 30°)`. Select eligible pixels within 30° of the highest-scoring center. If those selected pixels occupy at least 15% of the opaque sample, combine that center with the selected pixels' independent 85th-percentile saturation and value, then convert the HSV color back to rounded RGB.

For a cover without a substantial colorful family, retain the original neutral fallback: round each RGB channel to a bucket of 64 and average the original RGB values in the most common bucket. If there are no usable pixels or the cover cannot be read, use the app's paper and ink colors. Compute WCAG relative luminance for a derived color and choose whichever of black or white has the larger contrast ratio. Cache the result by cover URL; a stale image load cannot recolor a newer record. No color is keyed to an album, record, or label.

### Layout and overflow

Render a dedicated overlay element above the existing UI. Its top and bottom rows reuse the current status bar's 3rem height and 1.25rem horizontal inset. All four corner labels share the status label's DM Mono 1.1rem, weight 400, uppercase, and 0.2em letter spacing without per-corner overrides or reduced opacity. The top-left label uses the normal Play status format, `Play MM:SS`, with the advancing screensaver clock; the top-right label is only `Side A/B` for the current side. Center two separate lines in the middle with a 1.8rem gap. The artist uses normal 700 4.8rem/1.12 Gloock with zero letter spacing. The song uses normal 400 8.4rem/1.16 Fraunces with zero letter spacing. For either line that exceeds its available width, show a seamless scrolling duplicate separated by a gap. Re-measure after fonts load, on resize, and when the text changes. Respect reduced-motion preference.

## Risks / Trade-offs

- [Missing or unreadable cover] → Show the established paper/ink palette until a valid cover can be sampled.
- [A small vivid accent dominates the hue score] → Require the winning family to cover at least 15% of opaque pixels; otherwise use the neutral RGB bucket result.
- [Browser reload during playback] → Start the UI's 10-second idle countdown on entering Play, avoiding an immediate overlay over a newly opened screen.
- [Track or cover changes during asynchronous image loading] → Check the active cover URL before applying the computed palette.

## Migration Plan

No data migration is needed. The UI files deploy together; removing the overlay markup, styles, and client state reverts the change. Remove the temporary `previews/` directory and the `examples/` color and font experiments once their implementations are transferred into the UI.

## Open Questions

None.
