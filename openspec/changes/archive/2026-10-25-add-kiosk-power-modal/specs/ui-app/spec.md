## MODIFIED Requirements

### Requirement: Hidden kiosk exit control
The UI SHALL retain the invisible touch target in the persistent top bar between the mode label and stylus info, without changing its visible appearance or sizing. Touch or keyboard activation SHALL open a native HTML dialog inside the app screen with the centered question `Are you sure you want to exit?` and buttons ordered Cancel, Exit, Shutdown. The dialog SHALL have no visible heading or status text. Cancel SHALL receive initial focus, keyboard focus SHALL remain within the open modal, and dismissal SHALL restore focus to the trigger.

#### Scenario: Hidden control opens power options
- **WHEN** the hidden control is activated by touch or keyboard
- **THEN** the power dialog SHALL open and focus Cancel without sending an action request
- **AND** the invisible control SHALL retain no visible text, border, or background

#### Scenario: Safe dismissal
- **WHEN** the user activates Cancel, presses Escape, or clicks the backdrop while no action is pending
- **THEN** the dialog SHALL close, restore focus to the trigger, and send no destructive request
- **AND** clicking within the dialog SHALL NOT dismiss it

#### Scenario: Focus containment
- **WHEN** the user navigates with Tab or Shift+Tab while the dialog is open
- **THEN** focus SHALL remain inside the dialog

## ADDED Requirements

### Requirement: Immediate power action dismissal
Exit SHALL immediately send `POST /kiosk/exit` and Shutdown SHALL immediately send `POST /shutdown`, with no second confirmation. Selecting either action SHALL immediately close the modal without showing preview, progress, or success text. Repeated submissions and reopening SHALL be blocked while the real action is pending or accepted. Accepted responses SHALL contain `{ "success": true }`. HTTP/JSON failures SHALL release the pending guard and log a diagnostic without reopening the modal. Connection loss, invalid acknowledgement, or client timeout SHALL log an unconfirmed outcome and SHALL NOT automatically retry.

#### Scenario: Action is pending or accepted
- **WHEN** either real action is submitted
- **THEN** the modal SHALL close immediately and exactly one request SHALL be sent to its endpoint
- **AND** pending or accepted actions SHALL prevent duplicate submissions and reopening without visible status text

#### Scenario: Request fails
- **WHEN** an action returns an error
- **THEN** the pending guard SHALL be released and an error diagnostic SHALL be logged without reopening the dialog

#### Scenario: Connection loss
- **WHEN** the request loses its connection, times out, or cannot yield a valid acknowledgement
- **THEN** the UI SHALL log the outcome as unconfirmed and release the pending guard without reopening or automatically retrying

### Requirement: Boardless power preview
In boardless mode, `/#power-options` SHALL open the dialog. Both actions SHALL simulate locally, with no request to `/kiosk/exit` or `/shutdown`, regardless of whether the modal was opened by hash or trigger.

#### Scenario: Preview actions
- **WHEN** Exit or Shutdown is selected in boardless mode
- **THEN** the dialog SHALL close immediately without showing any preview message
- **AND** the trigger SHALL remain usable without a destructive request

#### Scenario: Board mode debug hash
- **WHEN** `#power-options` is used without the boardless marker
- **THEN** the UI SHALL NOT automatically open the dialog
