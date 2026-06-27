## Why

The frontend currently risks applying a root `<html>` font-size adjustment outside boardless mode, which can affect the fixed 800x480 board UI layout. Normal board mode should preserve the browser/default root font sizing unless boardless simulation explicitly needs an override.

## What Changes

- Set the `<html>` font size attribute/style only while the UI is running in boardless mode.
- Ensure normal board mode does not set a font size on the `<html>` element at all.
- Preserve boardless mode's ability to adjust root font sizing for development or simulation readability.

## Capabilities

### New Capabilities

### Modified Capabilities
- `ui-app`: Root HTML font-size behavior changes so boardless mode may set it, while normal board mode must leave it unset.
- `ui-design-system`: Rem-based root font-size calculation is scoped to boardless mode instead of applying globally.

## Impact

- Affects frontend mode/environment detection and root document styling in `ui/`.
- May require tests or browser checks for both boardless and normal board modes.
