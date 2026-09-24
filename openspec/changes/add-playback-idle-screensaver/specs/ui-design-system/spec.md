## MODIFIED Requirements

### Requirement: Design system typography — three font families
The UI SHALL use three core self-hosted font families: Gloock (display headings and numbers), Fraunces (body text and album titles in italic), and DM Mono (metadata, labels, and buttons, always uppercase with letter-spacing). It SHALL also self-host Roboto Serif as the playback screensaver's artist and song font.

#### Scenario: Font-face declarations exist
- **WHEN** the stylesheet is loaded
- **THEN** @font-face rules SHALL define Gloock (400), Fraunces (normal 400-900, italic 400-700), DM Mono (400, 500), and Roboto Serif (normal variable 100-900) loading from the `fonts/` directory

#### Scenario: Artist names use Gloock in the normal record view
- **WHEN** a record is displayed in the normal record view
- **THEN** the artist name SHALL render in Gloock serif at 28px

#### Scenario: Album titles use Fraunces italic
- **WHEN** a record is displayed
- **THEN** the album title SHALL render in Fraunces italic at 24px with color `var(--amber-deep)`

#### Scenario: Metadata uses DM Mono uppercase
- **WHEN** the record ID or mode label is displayed
- **THEN** it SHALL render in DM Mono, uppercase, with letter-spacing of at least 0.15em

#### Scenario: Screensaver uses local Roboto Serif
- **WHEN** the playback screensaver displays its artist and song
- **THEN** both lines SHALL render from the self-hosted Roboto Serif files at weights 700 and 300 respectively
