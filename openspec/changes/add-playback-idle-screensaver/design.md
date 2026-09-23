## Context

The UI is a fixed 800×480, three-file browser app. `setMode` owns mode transitions, `render` updates the Play view, WebSocket `status` messages provide elapsed playback time, and track selection already resolves a current side and track. Album covers are served from the same origin. The approved preview established the visual layout and a 64×64 canvas color sampling method.

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

Load the current same-origin cover into a 64×64 canvas. Ignore pixels with alpha below 200, round each RGB channel to a bucket of 64, and average the original RGB values in the most common bucket. Compute WCAG relative luminance for that color and select whichever of black or white has the larger contrast ratio. Cache the result by cover URL. A missing or unreadable cover uses the app's existing paper and ink colors; a stale image load cannot recolor a newer record.

### Layout and overflow

Render a dedicated overlay element above the existing UI. Its top and bottom rows reuse the current status bar's 3rem height, 1.25rem horizontal inset, and 1.1rem DM Mono text. The top-left label describes the current side and the top-right shows playback time. Center two separate lines in the middle with a 1.8rem gap, using Gloock 3.8rem for artist and upright Fraunces 5.2rem for song. For either line that exceeds its available width, show a seamless scrolling duplicate separated by a gap. Re-measure after fonts load, on resize, and when the text changes. Respect reduced-motion preference.

## Risks / Trade-offs

- [Missing or unreadable cover] → Show the established paper/ink palette until a valid cover can be sampled.
- [Browser reload during playback] → Start the UI's 10-second idle countdown on entering Play, avoiding an immediate overlay over a newly opened screen.
- [Track or cover changes during asynchronous image loading] → Check the active cover URL before applying the computed palette.

## Migration Plan

No data migration is needed. The UI files deploy together; removing the overlay markup, styles, and client state reverts the change. Remove the temporary `previews/` directory once the feature is implemented.

## Open Questions

None.
