## Context

The app is a dependency-free HTML/CSS/JavaScript kiosk with a Flask API and a 50rem × 30rem layout (800×480 at the Pi's default 16px root). Boardless mode uses a smaller physical preview scale. The invisible top-bar button currently calls `window.confirm`; Exit flushes stylus hours then schedules SIGTERM to the kiosk runner, whose trap closes Chromium and the API. `/shutdown` currently returns success without acting.

## Goals / Non-Goals

**Goals:** Provide accessible vintage power options with immediate Exit/Shutdown actions, reliable persistence and JSON failures, guarded systemd poweroff, boardless local previews, screensaver coordination, and reviewable browser evidence.

**Non-Goals:** Change the top-bar appearance, add another confirmation, redesign other screens, run real poweroff locally, sync delta specs, or archive this change.

## Decisions

- Use `dialog.showModal()` labelled by the confirmation question for browser focus containment and inert background. Put the dialog in an explicit `#app-screen` parent. Its 50rem × 30rem overlay is fixed to the app's top-left origin, with a transparent native backdrop outside that screen. Center a separate panel within this app-sized overlay; do not center against the browser viewport. Set Cancel focus explicitly and restore the trigger on close. Keep the dialog ID distinct from the preview hash, finish dismissal synchronously, and ignore a queued close event after reopening. Use standard button clicks for keyboard/touch; dismiss only when pointer start and end are outside the panel.
- Keep the panel 36rem wide with a square ink border, paper background, centered Fraunces question `Are you sure you want to exit?`, and DM Mono buttons. Remove the heading and status area. Use paper/ink for Cancel, paper/red-ink for Exit, and red-ink/paper for Shutdown. Remove the inset focus outline without adding an underline. Preserve normal board font sizing; use browser-only root overrides for 800×480 verification.
- Close the modal immediately on Exit/Shutdown, without preview, progress, or success text. Boardless actions stop locally after dismissal. In board mode, maintain pending state after closing to block duplicates/reopening until a failure or timeout; accepted actions stay locked while the app exits. Log JSON failures or unconfirmed connection loss to the console and release the pending guard without reopening or automatically retrying. The client timeout is 15 seconds. The boardless-only `#power-options` route opens the dialog over Standby.
- Cancel the screensaver activation timer and hide its overlay on open. Guard both scheduling and render paths while the dialog is open, including WebSocket updates. On close, set last interaction to now and schedule a new ten-second inactivity interval.
- Gate `/shutdown` on `KIOSK_SHUTDOWN_ENABLED=true`, non-boardless mode, Linux, and an IP loopback peer (do not trust forwarding headers). Flush pending usage before `subprocess.run(["sudo", "-n", "/usr/bin/systemctl", "poweroff"], check=True, timeout=5, capture_output=True)`. Return JSON 403 for disabled actions and 500 for persistence or command failures; return `{ "success": true }` after acceptance. Gate Exit on enabled/non-boardless state and retain its runner termination mechanism. The stylus tracker must report false persistence results so these actions can abort, including when the database silently updates no row.
- Add focused Node VM tests for UI state/action behavior and mocked Python API tests for guards, order, failures, and runner termination. Exercise real focus, backdrop, touch, computed styles, screensaver timing, and mocked network behavior with headed playwright-cli; keep the dashboard and modal visible.

## Risks / Trade-offs

- Poweroff or Exit can sever the connection before response → log an unconfirmed outcome and allow a deliberate retry; no automatic retries or visible post-action text.
- Incorrect sudoers configuration → fixed command with `sudo -n` fails promptly; document a narrowly scoped NOPASSWD rule, with no local permission edits.
- Accepted poweroff cannot prove hardware completion → local tests mock system calls; actual Pi poweroff remains a documented acceptance check.
- Tracker previously ignored unsuccessful persistence → return a success flag without discarding pending seconds; abort both power actions if persistence fails.

## Migration Plan

Deploy the code on Raspberry Pi OS with systemd and configure the kiosk user's passwordless poweroff permission. The existing kiosk script already enables kiosk shutdown. Rollback uses the previous app revision; no schema migration is required.

## Open Questions

None. Actions execute from this modal without a second confirmation.
