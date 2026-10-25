## ADDED Requirements

### Requirement: Vintage power dialog
The power dialog SHALL belong to the app screen and center its panel within that screen, including when the browser viewport is much larger than the app. Its dark overlay SHALL cover only the 50rem × 30rem app screen. The panel SHALL use rem-based dimensions, square corners, a paper surface with ink border, the centered Fraunces question `Are you sure you want to exit?`, and DM Mono buttons, without a heading or status area. Buttons SHALL appear left to right as Cancel (paper fill, ink text), Exit (the same paper fill with `--red-ink` text), and Shutdown (`--red-ink` fill, paper text). The buttons SHALL have no added focus outline or underline.

#### Scenario: Power dialog at both scales
- **WHEN** power options are shown at the existing boardless scale or Pi-equivalent 800×480 scale
- **THEN** the centered question and three buttons SHALL fit inside the main app screen without clipping
- **AND** the requested fill colors, fonts, square corners, and undecorated focus styling SHALL be present

#### Scenario: Browser viewport exceeds app screen
- **WHEN** the app runs at its boardless scale in a wide desktop browser
- **THEN** the panel SHALL remain centered within the app screen at the top left
- **AND** the dark overlay SHALL NOT extend beyond the app screen
