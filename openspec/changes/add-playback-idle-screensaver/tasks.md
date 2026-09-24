## 1. Screensaver UI

- [x] 1.1 Add the full-screen overlay markup with separate artist and song lines, corner labels, and an accessible dismissal target.
- [x] 1.2 Style the overlay with the current status bar's typography in all four corners, separate artist and song lines, overflow marquee, and reduced-motion behavior.
- [x] 1.3 Put the advancing `Play MM:SS` label in the top-left corner and the current `Side A/B` label alone in the top-right corner.
- [x] 1.4 Make overflowing lines scroll across the full screen width with repeated copies and no edge fade.
- [x] 1.5 Keep song titles in their original casing while matching the selected preview typography.
- [x] 1.6 Keep deep descenders visible in screensaver lines while retaining horizontal marquee clipping.
- [x] 1.7 Bundle Roboto Serif's variable upright language subsets and license, and load both chosen weights locally.
- [x] 1.8 Match the live screensaver's type sizes, weights, spacing, and half-screen marquee gap to the selected playground appearance.

## 2. Playback behavior

- [x] 2.1 Add Play-only idle timing and touch dismissal that resets the 10-second countdown and prevents touches from activating underlying controls.
- [x] 2.2 Bind the overlay to the selected track artist, song, album, side, and advancing playback time.
- [x] 2.3 Compute and cache a dominant color from each current cover and select black or white text by contrast, with a fallback for unreadable covers.
- [x] 2.4 Replace the primary RGB bucket palette with the automatically selected bright hue family, retaining the RGB bucket fallback for covers without a substantial colorful family.

## 3. Finish

- [x] 3.1 Remove the temporary `previews/` directory after transferring its implementation into the UI.
- [x] 3.2 Remove the temporary `examples/` color experiments after transferring the selected algorithm into the UI.
- [x] 3.3 Keep a standalone font playground with editable song and artist text and populated font selectors.
- [x] 3.4 Include all 68 families from the selected Google Fonts filter, add supported weight selectors for both lines, and prevent preview descender clipping.
- [x] 3.5 Add independent font size and letter spacing controls, show the resulting CSS, and let users copy it.
- [x] 3.6 Move the playground to `exp/font-playground.html` and give scrolling repeats a half-screen-width gap.
- [x] 3.7 Default the playground to `Cristin Milioti` and `Always Crashing In The Same Car` in Roboto Serif 700/4.6rem and 300/8rem, with zero letter spacing and initial font loading.
- [x] 3.8 Use the same bundled Roboto Serif files in the playground and omit a remote import from copied CSS for that local family.
