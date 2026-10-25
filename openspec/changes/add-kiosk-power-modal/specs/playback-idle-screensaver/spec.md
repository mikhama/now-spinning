## ADDED Requirements

### Requirement: Power dialog suspends screensaver
The UI SHALL hide the screensaver and suspend its activation while power options are open, including while processing playback events or a pending action. Dismissal SHALL restart the inactivity period from the dismissal time.

#### Scenario: Modal outlasts idle threshold
- **WHEN** the power dialog remains open in Play for more than ten seconds
- **THEN** the screensaver SHALL remain hidden

#### Scenario: Modal dismissed during Play
- **WHEN** power options are dismissed during Play
- **THEN** the screensaver SHALL remain hidden for a fresh ten seconds of inactivity before it can activate
