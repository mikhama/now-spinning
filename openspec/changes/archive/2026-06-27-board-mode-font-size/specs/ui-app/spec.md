## ADDED Requirements

### Requirement: Boardless-only root font-size marker
The UI SHALL mark the `<html>` element as boardless only when the application is served in boardless mode, and SHALL NOT set or enable root `<html>` font-size styling in normal board mode.

#### Scenario: Normal board mode leaves root font-size unset
- **WHEN** the UI document is served without `BOARDLESS_MODE=true`
- **THEN** the `<html>` element SHALL NOT include a boardless-mode marker
- **AND** no application stylesheet or inline style SHALL set `font-size` on the unmarked `<html>` element

#### Scenario: Boardless mode enables root font-size styling
- **WHEN** the UI document is served with `BOARDLESS_MODE=true`
- **THEN** the `<html>` element SHALL include a boardless-mode marker
- **AND** the application stylesheet SHALL apply the calculated root font-size only through that boardless-mode marker
