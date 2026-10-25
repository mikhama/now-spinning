# Verification — 25 October 2026

The implementation and all twelve tasks, including the requested visual
revisions, are complete. This change remains in
`openspec/changes/add-kiosk-power-modal/`; its delta specs have not been synced
or archived.

## Automated validation

- `node --test tests/ui_app_*.test.js`: **33 passed**, including 12 targeted power
  dialog tests. Coverage includes local simulations, focus wrapping/restoration,
  safe dismissal, delayed native-close events and rapid reopening, duplicate
  prevention, API errors, unconfirmed connection loss/malformed acknowledgements,
  the 15-second client timeout, and screensaver suspension/restart.
- `BOARDLESS_MODE=false python -m pytest -q tests/test_power_api.py tests/test_linking_api.py tests/test_stylus_hours.py`:
  **67 passed, 15 subtests passed**. Tests mock poweroff, timers, and signals,
  cover Linux/loopback/enabled/boardless gates (including spoofed forwarding
  headers), fixed command/timeout, persistence order, unsuccessful database
  writes, command errors/timeouts, JSON failures, and existing Exit behavior.
- `openspec validate add-kiosk-power-modal --strict`: **passed**.
- `git diff --check`: **passed**.

The temporary Python environment was `/private/tmp/now-spinning-power-venv/`.
The initial full Python suite also ran: **149 passed, 93 subtests passed, 67 failures**,
all in existing PN532 I2C driver tests. An unchanged `HEAD` archive in
`/private/tmp/now-spinning-power-baseline/` reproduced the same **67 failures**
(139 passed, 78 subtests passed without the new tests). Those tests retain an
I2C class imported while `smbus2.SMBus` is mocked to `None`; subsequent patches
resolve another module instance. No NFC driver/test changes were made here.

## Headed browser verification

Used `playwright-cli` 0.1.17 with installed Chrome (`--headed --browser=chrome`),
session `power-options`, and opened the dashboard with `playwright-cli ... show`.
The bundled Chromium executable was unavailable. The boardless server runs at
`http://127.0.0.1:5000/`; the final page is `/#power-options` with the modal open.

`playwright-cli -s=power-options run-code --filename=tests/power_options.browser.js`
completed successfully. It verified:

- Hidden trigger opening, Cancel/overlay/Escape dismissal, inside click and
  drag-out protection, initial Cancel focus, Tab/Shift+Tab containment, focus
  restoration, and Enter/Space activation including rapid reopen.
- The exact centered question `Are you sure you want to exit?`, no heading,
  no focus border or underline, and no status area.
- Both boardless actions close immediately without any message and send zero
  destructive requests.
- The overlay matches the app screen's origin and dimensions, and the panel
  remains centered inside that screen even in a 1600×1000 browser viewport.
- Button order, paper fill for Cancel and Exit, red Exit text, red-ink/paper
  Shutdown treatment, square corners, DM Mono labels, and no clipping.
- Mocked Shutdown/Exit requests close immediately, prevent duplicate submissions
  and reopening while pending, and keep the dialog closed after errors or success.
- JSON failures and unconfirmed connection loss produce console diagnostics,
  release the pending guard, and never automatically retry.
- Screensaver hidden after 12 seconds with the dialog open; hidden through
  9,999 milliseconds after dismissal and visible at 10,000 milliseconds.
- Touch trigger, both touch simulations, touch Cancel, and zero destructive
  requests in a separate touch-enabled context. All three buttons dismiss the modal.

All browser power requests were intercepted. No real poweroff or process
termination was performed. Expected mocked HTTP/network failures and the
existing missing `favicon.ico` appear in browser diagnostics. The screensaver
clock is paused before boundary checks so browser/tool overhead cannot advance
the 9,999/10,000 millisecond assertions.

## Display sizing

Verified:

- Boardless scale: 418×251 viewport,
  root font 8.34783px, panel approximately 301×111 pixels.
- Pi-equivalent display: 800×480 viewport,
  browser-only 16px root-font override, panel 576×212 pixels.
- Wide browser: 1600×1000 viewport
  with the overlay and panel contained within the 417×250 app screen.

Normal board-mode application root font sizing is unchanged. The sizing
override exists only in the browser verification script.

## Hardware acceptance

Actual Pi poweroff remains an explicit hardware acceptance check, outside local
verification. README documents systemd, the exact passwordless sudoers rule,
and checking that Shutdown powers off cleanly and persisted stylus usage survives
the next boot. Exit's runner SIGTERM path remains intact, including the existing
shell trap that terminates the API and Chromium; confirm desktop return on Pi.
