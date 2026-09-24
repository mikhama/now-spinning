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

Read the active record, side, and track from existing state when the overlay opens or Play data changes. Use `track.artist` when it has non-whitespace text; otherwise use `record.artist`. Show `track.title` alone on the song line in its original casing, even when the normal Play view appends a track artist to its track label. Use server playback time when present; while it is unavailable or between updates, advance an elapsed display from the latest known time and wall clock.

### Cover palette

Load the current same-origin cover into a 64×64 canvas and ignore pixels with alpha below 200. Convert each remaining RGB pixel to HSV. Eligible colorful pixels have saturation at least 0.28 and value at least 0.30. Score hue centers from 0° through 355° in 5° steps: each eligible pixel contributes its saturation multiplied by `max(0, 1 - circular hue distance / 30°)`. Select eligible pixels within 30° of the highest-scoring center. If those selected pixels occupy at least 15% of the opaque sample, combine that center with the selected pixels' independent 85th-percentile saturation and value, then convert the HSV color back to rounded RGB.

For a cover without a substantial colorful family, retain the original neutral fallback: round each RGB channel to a bucket of 64 and average the original RGB values in the most common bucket. If there are no usable pixels or the cover cannot be read, use the app's paper and ink colors. Compute WCAG relative luminance for a derived color and choose whichever of black or white has the larger contrast ratio. Cache the result by cover URL; a stale image load cannot recolor a newer record. No color is keyed to an album, record, or label.

### Layout and overflow

Render a dedicated overlay element above the existing UI. Its top and bottom rows reuse the current status bar's 3rem height and 1.25rem horizontal inset. All four corner labels share the status label's DM Mono 1.1rem, weight 400, uppercase, and 0.2em letter spacing without per-corner overrides or reduced opacity. The top-left label uses the normal Play status format, `Play MM:SS`, with the advancing screensaver clock; the top-right label is only `Side A/B` for the current side. Center two separate lines in the middle with a 1.8rem gap. Match the selected playground typography: artist normal 700 4.6rem/1.12 Roboto Serif and song normal 300 8rem/1.16 Roboto Serif, both with zero letter spacing and no uppercase transform. Keep the text area flush with both screen edges. Clip horizontal overflow for marquee motion while allowing vertical glyph overflow, so descenders such as `y` remain visible. For either line that exceeds the screen width, separate the identical copies by half the screen width and translate by the first copy's width plus that gap for a continuous newsline. Do not mask or fade the edges. Re-measure after the local font loads, on resize, and when the text changes. Respect reduced-motion preference.

Bundle Roboto Serif's upright variable WOFF2 files in `ui/fonts/` with their Open Font License. The four Latin and Cyrillic subsets from the Google Fonts CSS2 response cover weights 100–900 and use local `@font-face` rules with their original Unicode ranges. The live screensaver and the playground load these local files; other Google Fonts choices in the playground remain network-loaded.

### Font playground

Keep `exp/font-playground.html` as a standalone preview of the screensaver. Its song text uses the entered capitalization. Both artist and song font selectors contain the current app faces plus the 68 families shown by the linked Google Fonts filter for Cyrillic and Latin Serif/Slab fonts, captured from the rendered catalog on 24 September 2026. Each line has its own weight selector, populated only with that family's upright weights from the Google Fonts catalog metadata (or from the included local face declarations). Each line also has numeric font size in rem and letter spacing in em controls. Initialize the example text to `Cristin Milioti` and `Always Crashing In The Same Car` and the type to Roboto Serif: artist weight 700, size 4.6rem, line height 1.12, letter spacing 0em; song weight 300, size 8rem, line height 1.16, letter spacing 0em. Load both selected weights from the bundled font when the page opens. Re-measure text overflow as these values change. In this playground preview, separate scrolling copies by 50% of the preview screen width and translate by the first copy's width plus that gap for a seamless loop. Display CSS for both screensaver selectors with the chosen family, weight, size, line height, and letter spacing; include a Google Fonts import only when a remote family is selected and offer a copy button with a manual-selection fallback. Load other selected Google families through the CSS2 API. Other Google-hosted choices need an internet connection; the app fonts remain available offline. Use the same horizontal-only overflow clipping as the live screen so long descenders remain visible.

## Risks / Trade-offs

- [Missing or unreadable cover] → Show the established paper/ink palette until a valid cover can be sampled.
- [A small vivid accent dominates the hue score] → Require the winning family to cover at least 15% of opaque pixels; otherwise use the neutral RGB bucket result.
- [Browser reload during playback] → Start the UI's 10-second idle countdown on entering Play, avoiding an immediate overlay over a newly opened screen.
- [Track or cover changes during asynchronous image loading] → Check the active cover URL before applying the computed palette.

## Migration Plan

No data migration is needed. The UI files deploy together; removing the overlay markup, styles, and client state reverts the change. Remove the temporary `previews/` directory and the `examples/` color experiments once their implementations are transferred into the UI. Keep the font playground for future typography choices.

## Open Questions

None.
