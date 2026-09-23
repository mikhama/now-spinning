## 1. Screensaver UI

- [x] 1.1 Add the full-screen overlay markup with separate artist and song lines, corner labels, and an accessible dismissal target.
- [x] 1.2 Style the overlay with the current status bar's typography in all four corners, 5.7rem artist and 7.8rem song text, overflow marquee, and reduced-motion behavior.

## 2. Playback behavior

- [x] 2.1 Add Play-only idle timing and touch dismissal that resets the 10-second countdown and prevents touches from activating underlying controls.
- [x] 2.2 Bind the overlay to the selected track artist, song, album, side, and advancing playback time.
- [x] 2.3 Compute and cache a dominant color from each current cover and select black or white text by contrast, with a fallback for unreadable covers.

## 3. Finish

- [x] 3.1 Remove the temporary `previews/` directory after transferring its implementation into the UI.
