## ADDED Requirements

### Requirement: Hidden kiosk exit control
The UI SHALL provide an invisible touch target in the persistent top bar between the mode label and stylus info. The target SHALL take approximately half the horizontal size of the stylus info area, SHALL NOT alter the visible top-bar appearance, and SHALL ask for browser-native confirmation before requesting kiosk exit.

#### Scenario: Hidden exit control is present
- **WHEN** the UI loads
- **THEN** the top bar SHALL contain an invisible interactive control between the mode label and stylus info
- **AND** the control SHALL NOT render visible text, border, or background

#### Scenario: User cancels kiosk exit
- **WHEN** the hidden exit control is activated
- **AND** the user cancels the browser-native confirmation dialog
- **THEN** the UI SHALL NOT send a kiosk exit request

#### Scenario: User confirms kiosk exit
- **WHEN** the hidden exit control is activated
- **AND** the user confirms the browser-native confirmation dialog
- **THEN** the UI SHALL send a `POST` request to the kiosk exit endpoint
