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
The screensaver SHALL show the current track artist and song on separate, centered lines in the middle of the screen. It SHALL use the track's artist when provided and otherwise use the record's artist. The artist SHALL use 5.7rem Gloock and the upright song SHALL use 7.8rem Fraunces. The lines SHALL have no divider and no cover miniature. The top-right corner SHALL show elapsed playback time. All four corner labels SHALL share the status label's DM Mono font, 1.1rem size, weight 400, uppercase style, 0.2em letter spacing, and horizontal inset, with no reduced opacity.

#### Scenario: Corner labels use status typography
- **WHEN** the screensaver is visible
- **THEN** its four corner labels SHALL have the same font size, weight, letter spacing, and opacity as the status label
- **AND** the artist and song SHALL use 5.7rem and 7.8rem font sizes respectively

#### Scenario: Track artist differs from record artist
- **WHEN** the current track provides an artist that differs from the record artist
- **THEN** the artist line SHALL show the track artist and the song line SHALL show only the track title

#### Scenario: Track artist is absent
- **WHEN** the current track has no artist
- **THEN** the artist line SHALL show the record artist

#### Scenario: Playback time advances
- **WHEN** the screensaver is visible during Play
- **THEN** its top-right elapsed time SHALL advance and use the latest server playback time when available

#### Scenario: Track changes
- **WHEN** the selected track changes during Play
- **THEN** the artist and song lines SHALL reflect the new track

### Requirement: Long text motion
The screensaver SHALL keep artist and song on separate single lines. A line that is wider than its container SHALL scroll horizontally like a newsline; a line that fits SHALL remain centered and still. The complete text SHALL remain available to assistive technology.

#### Scenario: Long song title
- **WHEN** the song title exceeds the available width
- **THEN** the song line SHALL scroll continuously without clipping the title permanently

#### Scenario: Short artist name
- **WHEN** the artist name fits the available width
- **THEN** the artist line SHALL remain centered without scrolling

#### Scenario: Reduced motion preference
- **WHEN** the browser requests reduced motion
- **THEN** marquee animation SHALL stop
