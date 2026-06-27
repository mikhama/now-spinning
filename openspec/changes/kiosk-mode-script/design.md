## Context

The app is currently started from the project virtualenv with `python -m api.main`, and the Flask server serves the UI from `ui/` on port `5000`. Kiosk deployments should not require a user to activate `env/`, remember the Python command, wait for the server manually, and then launch a browser with the correct flags.

The requested entry point is `./bin/run_kiosk.sh`, so the implementation should be a repository-local shell script that works from any current directory and starts the existing app command without changing the app runtime model.

## Goals / Non-Goals

**Goals:**

- Provide one command that starts the app and opens `http://127.0.0.1:5000/` in browser kiosk mode.
- Use the repository virtualenv at `env/` for the app process.
- Keep the app process tied to the script so exiting or interrupting the script stops the server it started.
- Use the `chromium` browser command available on the target device.
- Document the command briefly in `README.md`.

**Non-Goals:**

- Do not introduce a process supervisor, systemd unit, or boot-time autostart.
- Do not change Flask routes, UI behavior, data storage, or boardless mode semantics.
- Do not make kiosk browser support fully cross-platform beyond practical Linux/Raspberry Pi usage.

## Decisions

- Implement `bin/run_kiosk.sh` as a POSIX shell script that resolves the repository root from the script path.
  - Rationale: the command should work when launched as `./bin/run_kiosk.sh` and should not depend on the caller's current directory.
  - Alternative considered: document a long inline command in the README. That keeps code smaller but does not satisfy the single-command requirement.

- Activate the repository virtualenv from `env/bin/activate` before starting the app with `python -m api.main`.
  - Rationale: the README already documents `env/` as the project environment, and the kiosk command should work without requiring a separate manual activation step.
  - Alternative considered: call the system `python` directly. That is simpler but can fail when dependencies are installed only in the project virtualenv.

- Wait for `http://127.0.0.1:5000/` to respond before launching the browser.
  - Rationale: kiosk mode should open to the app instead of a browser error page while Flask is still starting.
  - Alternative considered: sleep a fixed number of seconds. That is simpler but unreliable on slower hardware.

- Launch the browser with the `chromium` command.
  - Rationale: the target device uses Chromium, so a single explicit browser command keeps the script simple and predictable.
  - Alternative considered: discover multiple Chromium-family browser command names. That adds fallback logic that is not needed for this deployment.

- Launch the browser with kiosk-oriented Chromium flags and an isolated temporary user data directory.
  - Rationale: kiosk launches should not depend on an existing browser profile and should suppress first-run prompts where possible.
  - Alternative considered: reuse the default user profile. That can inherit prompts, sessions, or settings that interfere with kiosk startup.

## Risks / Trade-offs

- `chromium` is missing -> print a clear error explaining that Chromium must be installed or available on `PATH`.
- `env/bin/activate` is missing -> print a clear error explaining that the project virtualenv must be created and dependencies installed.
- Port `5000` is already occupied -> the app startup will fail or the readiness check may connect to the wrong process; keep this out of scope unless implementation discovers a safe existing-app detection path.
- Browser flags vary across Chromium builds -> use conservative, widely supported flags and avoid assuming every prompt can be suppressed.
- The browser may keep running after the script receives unusual termination signals -> trap common shell exits and clean up the server process the script started.

## Migration Plan

Add the script, make it executable, and update README usage documentation. Rollback is removing `bin/run_kiosk.sh` and the README note.
