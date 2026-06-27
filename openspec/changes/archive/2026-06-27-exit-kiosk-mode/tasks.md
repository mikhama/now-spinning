## 1. Kiosk Runner Lifecycle

- [x] 1.1 Update `bin/run_kiosk.sh` to enable kiosk shutdown for the app process via environment variable.
- [x] 1.2 Launch Chromium in the background, store `CHROMIUM_PID`, and wait on it to preserve kiosk script lifecycle.
- [x] 1.3 Extend the cleanup trap to terminate both `APP_PID` and `CHROMIUM_PID` when they are still running.

## 2. API Shutdown Endpoint

- [x] 2.1 Add a `POST /kiosk/exit` endpoint in `api/main.py`.
- [x] 2.2 Reject `/kiosk/exit` requests when kiosk shutdown is not explicitly enabled.
- [x] 2.3 When enabled, have `/kiosk/exit` request termination of the kiosk runner process and return `{ "success": true }`.

## 3. Hidden UI Control

- [x] 3.1 Add an invisible top-bar button in `ui/index.html` between `#mode-label` and `#stylus-info`.
- [x] 3.2 Style the hidden button in `ui/style.css` so it occupies roughly half the stylus info width without changing visible top-bar appearance.
- [x] 3.3 Add a click handler in `ui/app.js` that shows native confirmation and posts to `/kiosk/exit` only after confirmation.

## 4. Verification

- [x] 4.1 Add or update backend tests for disabled and enabled `/kiosk/exit` behavior without terminating the test process.
- [x] 4.2 Run the Python test suite.
- [x] 4.3 Run `sh -n bin/run_kiosk.sh`.
- [ ] 4.4 Manually verify in kiosk mode that confirming exit closes Chromium and stops the app.
