## Context

The app runs as a Flask server that serves a static three-file frontend. `bin/run_kiosk.sh` starts `python -m api.main` in the background, waits for readiness, and launches Chromium in kiosk mode in the foreground. The current cleanup trap stops the app process when the script exits, but there is no touchscreen path to request that exit from inside the kiosk UI.

The requested UI control should remain visually invisible and live in the top bar between `#mode-label` and `#stylus-info`. Because normal browser JavaScript cannot terminate OS processes, the frontend needs to ask the local Flask app to perform a gated shutdown action.

## Goals / Non-Goals

**Goals:**

- Provide an invisible top-bar touch target for exiting kiosk mode.
- Require explicit browser confirmation before sending the exit request.
- Make the backend endpoint unavailable unless kiosk shutdown is explicitly enabled by the kiosk runner.
- Ensure kiosk exit cleans up both the Flask app process and the Chromium process.

**Non-Goals:**

- Add visible UI, settings screens, icons, or new navigation.
- Shut down or reboot the Raspberry Pi operating system.
- Support remote administrative shutdown from other hosts.
- Replace the kiosk runner with a process supervisor.

## Decisions

1. Use native `window.confirm()` for confirmation.

   Rationale: the user asked for a simple default confirmation menu, and native confirmation blocks accidental taps with minimal UI code. Alternative considered: custom modal markup. Rejected because it would add visible styling and focus-management work without improving this small operator action.

2. Add a local `POST /kiosk/exit` endpoint guarded by an environment variable.

   Rationale: Flask can terminate or signal its parent process, while browser JavaScript cannot. The endpoint should return 404 or 403 unless explicitly enabled, so development mode does not expose a process kill action. Alternative considered: always expose the endpoint only on localhost. Rejected as insufficient because the app already serves local users and an explicit opt-in is clearer.

3. Have the endpoint signal the kiosk runner process instead of only exiting Flask.

   Rationale: if Flask exits by itself, Chromium may remain open on an error page or continue running. Signaling the parent kiosk script lets the existing cleanup trap become the single owner of process teardown. Alternative considered: endpoint directly kills Chromium by process lookup. Rejected because process lookup is more brittle than tracking the process started by the script.

4. Update `run_kiosk.sh` to run Chromium in the background and track `CHROMIUM_PID`.

   Rationale: the cleanup trap can then terminate both app and browser regardless of whether exit came from Ctrl-C, Chromium closing, or the UI shutdown endpoint. The script can wait on Chromium after launch to preserve the current foreground lifecycle.

## Risks / Trade-offs

- [Risk] A hidden touch target could be triggered accidentally. -> Mitigation: require native confirmation before the `POST` request.
- [Risk] A shutdown endpoint can be abused if exposed broadly. -> Mitigation: enable only via kiosk-runner environment and reject requests when disabled.
- [Risk] Signaling the wrong parent could terminate an unexpected shell in development. -> Mitigation: only enable the endpoint in kiosk mode and prefer terminating the recorded parent process from the kiosk-runner launch path.
- [Risk] Backgrounding Chromium changes script lifecycle behavior. -> Mitigation: track `CHROMIUM_PID`, wait for it after launch, and reuse the existing cleanup trap for all exit paths.
