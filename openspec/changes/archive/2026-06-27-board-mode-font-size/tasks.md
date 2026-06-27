## 1. Boardless Document Marker

- [x] 1.1 Add a backend helper that treats `BOARDLESS_MODE=true` as boardless mode using a case-insensitive exact match.
- [x] 1.2 Update the `/` route so the served `index.html` includes a boardless marker on `<html>` only when boardless mode is enabled.
- [x] 1.3 Verify the normal board response leaves the `<html>` tag unmarked.

## 2. Root Font-Size Styling

- [x] 2.1 Move the calculated root `font-size` rule from the unconditional `html` selector to the boardless-only root selector.
- [x] 2.2 Keep the screen sizing custom properties available without setting `html` font-size in normal board mode.
- [x] 2.3 Check that no inline style or other stylesheet rule sets `font-size` on an unmarked `<html>` element.

## 3. Verification

- [x] 3.1 Verify normal board mode serves the UI without a boardless marker and without application-defined `html` font-size.
- [x] 3.2 Verify boardless mode serves the UI with the marker and applies `calc(var(--screen-width) / 50 * var(--dpi-correction))` to the root font-size.
- [x] 3.3 Verify the UI still renders within the 800x480 viewport without scrolling in normal board mode.
