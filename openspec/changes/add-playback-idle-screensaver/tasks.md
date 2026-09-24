## 1. Screensaver UI

- [x] 1.1 Add the full-screen overlay markup with separate artist and song lines, corner labels, and an accessible dismissal target.
- [x] 1.2 Style the overlay with the current status bar's typography in all four corners, 4.8rem bold artist and 8.4rem regular song text with zero letter spacing, overflow marquee, and reduced-motion behavior.
- [x] 1.3 Put the advancing `Play MM:SS` label in the top-left corner and the current `Side A/B` label alone in the top-right corner.

## 2. Playback behavior

- [x] 2.1 Add Play-only idle timing and touch dismissal that resets the 10-second countdown and prevents touches from activating underlying controls.
- [x] 2.2 Bind the overlay to the selected track artist, song, album, side, and advancing playback time.
- [x] 2.3 Compute and cache a dominant color from each current cover and select black or white text by contrast, with a fallback for unreadable covers.
- [x] 2.4 Replace the primary RGB bucket palette with the automatically selected bright hue family, retaining the RGB bucket fallback for covers without a substantial colorful family.

## 3. Finish

- [x] 3.1 Remove the temporary `previews/` directory after transferring its implementation into the UI.
- [x] 3.2 Remove the temporary `examples/` color experiments after transferring the selected algorithm into the UI.
- [x] 3.3 Remove the temporary `examples/` font playground after applying the chosen typography.
