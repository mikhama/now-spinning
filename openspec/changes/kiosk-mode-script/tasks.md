## 1. Kiosk Script

- [x] 1.1 Create `bin/run_kiosk.sh` as an executable shell script.
- [x] 1.2 Resolve the repository root from the script location and activate `env/bin/activate`.
- [x] 1.3 Print a clear error if `env/bin/activate` is missing.
- [x] 1.4 Start the app with `python -m api.main` from the activated virtualenv.
- [x] 1.5 Add a readiness loop that waits for `http://127.0.0.1:5000/` before launching the browser.
- [x] 1.6 Check that `chromium` is available on `PATH` and print a clear error when it is missing.
- [x] 1.7 Launch `chromium` with kiosk flags pointed at `http://127.0.0.1:5000/`.
- [x] 1.8 Trap common script exits and interrupt signals to stop the app process started by the script.

## 2. Documentation

- [x] 2.1 Add a short README usage note for running kiosk mode with `./bin/run_kiosk.sh`.

## 3. Verification

- [x] 3.1 Run a shell syntax check for `bin/run_kiosk.sh`.
- [x] 3.2 Verify the script file has executable permissions.
- [x] 3.3 Validate the OpenSpec change artifacts.
