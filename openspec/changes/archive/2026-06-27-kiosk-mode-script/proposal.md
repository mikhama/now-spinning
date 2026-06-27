## Why

Running the app in a physical or unattended setup should be a single command that starts the app and opens the browser in kiosk mode. This removes manual startup steps and makes the project easier to deploy on a display device.

## What Changes

- Add a `./bin/run_kiosk.sh` script that launches the whole app and opens it in a browser using kiosk mode.
- Ensure the script handles the app startup flow consistently enough for local kiosk use.
- Add a short README note documenting how to run the kiosk script.

## Capabilities

### New Capabilities

- `kiosk-runner`: Covers launching the full app with a browser in kiosk mode from a repository script.

### Modified Capabilities

None.

## Impact

- Adds a new executable script under `bin/`.
- Updates README documentation with the kiosk command.
- May touch app startup assumptions if the existing dev/start command needs to be orchestrated by the script.
