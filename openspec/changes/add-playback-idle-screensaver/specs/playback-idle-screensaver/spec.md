## ADDED Requirements

### Requirement: Playback-only idle activation
The UI SHALL show the screensaver only in Play mode, after Play has been active for at least 10 seconds and the display has received no pointer interaction for at least 10 seconds. It SHALL hide the screensaver and cancel pending activation when leaving Play mode.

#### Scenario: Untouched playback
- **WHEN** Play has been active for 10 seconds and no pointer interaction occurred in that interval
- **THEN** the screensaver SHALL cover the normal UI

#### Scenario: Interaction delays activation
- **WHEN** a pointer interaction occurs during Play before the screensaver appears
- **THEN** the screensaver SHALL remain hidden until 10 seconds after that interaction

#### Scenario: Dismissal and reactivation
- **WHEN** the screensaver is visible and the display is touched
- **THEN** it SHALL dismiss without activating a control beneath it
- **AND** it SHALL reappear after a further 10 seconds of untouched Play

#### Scenario: Playback ends
- **WHEN** the UI leaves Play
- **THEN** the screensaver SHALL be hidden and SHALL NOT appear outside Play

### Requirement: Automatic cover palette
The screensaver SHALL derive its background color from the current record cover at runtime using a 64×64 canvas sample. It SHALL ignore pixels with alpha below 200, convert the remaining pixels to HSV, and consider pixels with saturation at least 0.28 and value at least 0.30 for colorful hue selection. It SHALL score hue centers from 0° through 355° in 5° steps. Each eligible pixel SHALL contribute `saturation × max(0, 1 − circular hue distance / 30°)` to a center's score. The winning center SHALL have the highest score.

If eligible pixels within 30° of the winning center cover at least 15% of the opaque sample, the background SHALL use the winning hue with the selected pixels' independent 85th-percentile saturation and value, converted to rounded RGB. If there are no eligible pixels or the selected family covers less than 15%, it SHALL average the original RGB values in the most common RGB bucket, formed by rounding each channel to the nearest multiple of 64. It SHALL choose black or white foreground text according to which has higher contrast against the derived background. It SHALL NOT use per-record or per-label color mappings.

#### Scenario: Cover has a substantial colorful hue family
- **WHEN** the current record has a readable cover image and the highest-scoring colorful hue family covers at least 15% of its opaque sample
- **THEN** the screensaver SHALL use that family's winning hue and 85th-percentile saturation and value as its background color
- **AND** it SHALL use the higher-contrast black or white as its foreground

#### Scenario: Cover has no substantial colorful hue family
- **WHEN** the current record has a readable cover image but has no eligible colorful pixels or its highest-scoring colorful hue family covers less than 15% of its opaque sample
- **THEN** the screensaver SHALL use the average original RGB color of the largest 64-step RGB bucket and the higher-contrast black or white foreground

#### Scenario: Cover is unavailable
- **WHEN** the current record cover cannot be read or has no opaque sampled pixels
- **THEN** the screensaver SHALL use the UI's paper and ink colors

#### Scenario: Cover changes
- **WHEN** the active record cover changes while the screensaver is visible
- **THEN** the background and foreground SHALL update from the new cover

### Requirement: Now-playing content and layout
The screensaver SHALL show the current track artist and song on separate, centered lines in the middle of the screen. It SHALL use the track's artist when provided and otherwise use the record's artist. It SHALL preserve the song title's source casing. The artist SHALL use normal 700 4.6rem/1.12 Roboto Serif with 0em letter spacing. The song SHALL use normal 300 8rem/1.16 Roboto Serif with 0em letter spacing and no uppercase text transformation. The lines SHALL have no divider and no cover miniature. The top-left corner SHALL show `Play` and elapsed playback time in the same `Play MM:SS` format as the normal Play status label. The top-right corner SHALL show only the current `Side A/B` label. All four corner labels SHALL share the status label's DM Mono font, 1.1rem size, weight 400, uppercase style, 0.2em letter spacing, and horizontal inset, with no reduced opacity.

#### Scenario: Corner labels use status typography
- **WHEN** the screensaver is visible
- **THEN** its four corner labels SHALL have the same font size, weight, letter spacing, and opacity as the status label
- **AND** the artist SHALL use 4.6rem Roboto Serif at weight 700 and the song SHALL use 8rem Roboto Serif at weight 300, both upright with zero letter spacing

#### Scenario: Top corners show Play status and side
- **WHEN** the screensaver is visible during Play on side B at elapsed time `01:24`
- **THEN** the top-left corner SHALL display `PLAY 01:24`
- **AND** the top-right corner SHALL display `SIDE B` without a `Now spinning` prefix

#### Scenario: Side changes while screensaver is visible
- **WHEN** the selected side changes from A to B during Play
- **THEN** the top-right corner SHALL update from `SIDE A` to `SIDE B`

#### Scenario: Track artist differs from record artist
- **WHEN** the current track provides an artist that differs from the record artist
- **THEN** the artist line SHALL show the track artist and the song line SHALL show only the track title

#### Scenario: Track artist is absent
- **WHEN** the current track has no artist
- **THEN** the artist line SHALL show the record artist

#### Scenario: Playback time advances
- **WHEN** the screensaver is visible during Play
- **THEN** its top-left elapsed time SHALL advance and use the latest server playback time when available

#### Scenario: Track changes
- **WHEN** the selected track changes during Play
- **THEN** the artist and song lines SHALL reflect the new track

#### Scenario: Mixed-case title from metadata
- **WHEN** the current track title is `Numb/Encore`
- **THEN** the song line SHALL preserve `Numb/Encore`

### Requirement: Long text motion
The screensaver SHALL keep artist and song on separate single lines. A line that is wider than the screen SHALL scroll horizontally like a newsline from one screen edge to the other, with no side inset or edge fade and with a gap equal to half the screen width between consecutive copies. Each animation cycle SHALL advance by one copy plus that gap. A line that fits SHALL remain centered and still. Horizontal clipping SHALL NOT cut off vertical glyph descenders. The complete text SHALL remain available to assistive technology.

#### Scenario: Long song title
- **WHEN** the song title exceeds the available width
- **THEN** the song line SHALL scroll continuously across the full screen width with a half-screen-width gap between repeats and no blurred or faded edges

#### Scenario: Short artist name
- **WHEN** the artist name fits the available width
- **THEN** the artist line SHALL remain centered without scrolling

#### Scenario: Reduced motion preference
- **WHEN** the browser requests reduced motion
- **THEN** marquee animation SHALL stop

#### Scenario: Descender remains visible
- **WHEN** a song title contains a letter with a deep descender such as `y`
- **THEN** its descender SHALL remain visible in both the screensaver and the playground preview

### Requirement: Self-hosted Roboto Serif
The UI SHALL serve Roboto Serif from its own `ui/fonts/` directory as upright variable WOFF2 files covering weights 100–900 and the Latin, Latin Extended, Cyrillic, and Cyrillic Extended subsets. The font license SHALL be included with the files. The screensaver and the playground's Roboto Serif option SHALL use these local files without a Google Fonts request.

#### Scenario: Screensaver font loads while offline
- **WHEN** the screensaver opens without internet access
- **THEN** its artist at weight 700 and song at weight 300 SHALL render from the local Roboto Serif files
- **AND** line overflow SHALL be re-measured after those fonts load

#### Scenario: Playground selects Roboto Serif
- **WHEN** either playground line selects Roboto Serif at an available weight
- **THEN** the corresponding local font file SHALL be used
- **AND** the copied CSS SHALL not require a Google Fonts import for that family

### Requirement: Font comparison playground
The project SHALL provide a standalone HTML font playground in `exp/` for the screensaver. It SHALL allow editing artist and song text independently. Each font selector SHALL list the current app faces and all 68 Google Fonts families shown by the linked Cyrillic + Latin Serif/Slab filter as of 24 September 2026. Each line SHALL have a separate weight selector offering only its selected family's available upright weights, plus independent font size and letter spacing controls. The initial selections SHALL be Roboto Serif weight 700, size 4.6rem, and 0em letter spacing for the artist and Roboto Serif weight 300, size 8rem, and 0em letter spacing for the song, with the corresponding fonts loaded locally on page open. The preview SHALL update as these controls change and re-measure whether each line needs to scroll. Scrolling copies in the playground SHALL have a gap equal to 50% of the preview screen width, with each cycle advancing by one copy plus that gap. The playground SHALL show CSS for both lines reflecting the current selections and SHALL offer a way to copy it. CSS for selected remote Google Fonts families SHALL include the required import; CSS for app-bundled families SHALL use the local declarations. The song preview SHALL preserve the text entered by the user without an uppercase transformation.

#### Scenario: Compare available fonts
- **WHEN** a user opens the playground's artist or song font selector
- **THEN** it SHALL contain the current app faces and all 68 families from the selected Google Fonts filter

#### Scenario: Open the default example
- **WHEN** a user opens the playground
- **THEN** the artist SHALL be `Cristin Milioti` in Roboto Serif at 700, 4.6rem, and 0em letter spacing
- **AND** the song SHALL be `Always Crashing In The Same Car` in Roboto Serif at 300, 8rem, and 0em letter spacing
- **AND** the generated CSS SHALL use the bundled Roboto Serif family without a Google Fonts import

#### Scenario: Change weight independently
- **WHEN** a user selects a font and weight for the artist or song
- **THEN** that line SHALL render in the chosen family's selected available upright weight without changing the other line

#### Scenario: Edit the song title
- **WHEN** a user enters `Ain't It Tragic` as the song title
- **THEN** the preview SHALL display `Ain't It Tragic` in that casing

#### Scenario: Tune size and spacing independently
- **WHEN** a user changes the artist font size or letter spacing
- **THEN** the artist preview SHALL update and its overflow SHALL be re-measured without changing the song settings

#### Scenario: Copy chosen CSS
- **WHEN** a user changes either line's typography settings
- **THEN** the displayed CSS SHALL include the current family, weight, size, line height, and letter spacing for both screensaver selectors
- **AND** the user SHALL be able to copy that CSS, including a Google Fonts import for any selected remote family

#### Scenario: Scrolling preview repeats
- **WHEN** a playground line is wider than the preview screen
- **THEN** its repeated copies SHALL be separated by a gap equal to half the preview screen width
- **AND** the animation SHALL advance by one copy plus that gap before restarting
