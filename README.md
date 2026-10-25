# now-spinning
Hobby project with Raspberry Pi.

## Prerequisites

To create a virtual environment:
```bash
python -m venv env
```

To activate the virtual environment:
```bash
source env/bin/activate
```

To deactivate the virtual environment:
```bash
deactivate
```

To install dependencies:
```bash
pip install -r requirements.in
```

## Usage

To run the app in kiosk mode on Pi:
```bash
./bin/run_kiosk.sh
```

### Power options

Tap the invisible area between the mode label and stylus information in the top
bar to open a centered **Are you sure you want to exit?** dialog within the app
screen. It offers **Cancel**, **Exit**, and **Shutdown**.
Exit closes the kiosk runner, API, and Chromium; Shutdown requests an orderly
Raspberry Pi poweroff. Selecting either action closes the dialog immediately,
without showing preview, progress, or success messages. Pending
stylus hours are saved first; if saving fails, the action is aborted. Cancel,
Escape, and touching the backdrop dismiss the idle dialog. The playback
screensaver pauses while it is open and waits a fresh ten seconds after dismissal.

Shutdown requires Raspberry Pi OS with systemd, a loopback request, boardless
mode disabled, and `KIOSK_SHUTDOWN_ENABLED=true` (set by the kiosk script).
The kiosk user must be allowed to run the exact poweroff command without a
password prompt. On the Pi, use `sudo visudo -f /etc/sudoers.d/now-spinning-poweroff`
and add the following rule, replacing `kioskuser` with the actual kiosk username:

```sudoers
kioskuser ALL=(root) NOPASSWD: /usr/bin/systemctl poweroff
```

The API runs the fixed argument list `sudo -n /usr/bin/systemctl poweroff`
without a shell, with a five-second timeout. See the
[systemctl poweroff documentation](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html#poweroff).
Disabled actions and command failures return JSON errors. If the connection is
lost before acknowledgement, the console records an unconfirmed outcome and
the app does not retry automatically; check the device before trying again.

### Start automatically on boot

On Raspberry Pi OS using the labwc desktop, open the desktop autostart file:

```bash
mkdir -p ~/.config/labwc
nano ~/.config/labwc/autostart
```

Add this line at the end, adjusting the paths if the project is installed elsewhere:

```bash
/home/<username>/code/now-spinning/bin/run_kiosk.sh >> /home/<username>/now-spinning.log 2>&1 &
```

The trailing `&` runs the script in the background. The script activates the
project's virtual environment and selects the project directory automatically.
Startup output is saved in `/home/<username>/now-spinning.log`.

Open the Raspberry Pi configuration menu:

```bash
sudo raspi-config
```

Using the arrow keys and Enter:

1. Select **1 System Options → S5 Boot → B2 Desktop**.
2. Return to **1 System Options → S6 Auto Login**.
3. Keep your preferred console login setting, then select **Yes** when asked
   whether to automatically log in to the desktop.
4. Select **Finish** and reboot.

On versions with a combined **S5 Boot / Auto Login** menu, select
**B4 Desktop Autologin** instead.

To reboot manually:

```bash
sudo reboot
```

See the [official Raspberry Pi kiosk guide](https://www.raspberrypi.com/tutorials/how-to-use-a-raspberry-pi-in-kiosk-mode/)
for more about labwc autostart.

## Development

To run the app in boardless mode:
```bash
BOARDLESS_MODE=true python -m api.main
```

To run the NFC demo in boardless mode:
```bash
BOARDLESS_MODE=true python -m exp.nfc_test
```

To debug all views:
- http://127.0.0.1:5000/#sync
- http://127.0.0.1:5000/#standby
- http://127.0.0.1:5000/#standby-error
- http://127.0.0.1:5000/#standby-not-found
- http://127.0.0.1:5000/#play
- http://127.0.0.1:5000/#link
- http://127.0.0.1:5000/#link-error
- http://127.0.0.1:5000/#re-link
- http://127.0.0.1:5000/#stylus
- http://127.0.0.1:5000/#stylus-error
- http://127.0.0.1:5000/#power-options

The power-options debug URL opens the dialog in boardless mode. Exit and
Shutdown both close it immediately without a message. Both simulate locally
and send no destructive requests, including when
the dialog is opened with the hidden trigger. The API rejects both real actions
in boardless mode even if kiosk shutdown is enabled.

Power-options verification:

```bash
node --test tests/ui_app_*.test.js
python -m pytest -q tests/test_power_api.py tests/test_linking_api.py tests/test_stylus_hours.py
# With the boardless server running in another terminal:
playwright-cli -s=power-options open 'http://127.0.0.1:5000/#power-options' --headed --browser=chrome
playwright-cli -s=power-options show
playwright-cli -s=power-options run-code --filename=tests/power_options.browser.js
```

The Python tests mock process termination and poweroff. The browser checks
intercept destructive endpoints while testing requests and errors, exercise
touch/keyboard/focus/screensaver behavior, and verify wide-browser, boardless,
and 800×480 layouts. Pi sizing
uses a browser-only 16px root-font override; application font sizing is unchanged.
Actual Pi poweroff remains a hardware acceptance check: with passwordless
permission configured, select Shutdown during playback and verify orderly poweroff
and that the last stylus usage was saved after the next boot. Verify Exit on the
Pi closes Chromium and returns to the desktop.

To compare screensaver fonts, weights, sizes, and letter spacing, open [the font playground](exp/font-playground.html) in a browser. It lists the 68 families from the linked Cyrillic + Latin Serif/Slab Google Fonts filter and provides CSS you can copy for both lines. The app fonts, including Roboto Serif, work offline; other Google Fonts choices need an internet connection.

Roboto Serif's variable WOFF2 subsets and Open Font License are in [`ui/fonts/`](ui/fonts/).

To send events in boardless mode (from another terminal):
```bash
# Scan a record
curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"32"}}' localhost:5000/events

# Turntable started spinning (boardless Play-mode test)
curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"play","time":"00:01"}}' localhost:5000/events

# Turntable stopped
curl -X POST -H "Content-Type: application/json" -d '{"event":"status","data":{"status":"stop"}}' localhost:5000/events

# Record not found
curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":"999"}}' localhost:5000/events

# NFC reading error
curl -X POST -H "Content-Type: application/json" -d '{"event":"scan","data":{"record_id":null}}' localhost:5000/events

# Link success
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_success","data":{"record_id":"1"}}' localhost:5000/events

# Link error
curl -X POST -H "Content-Type: application/json" -d '{"event":"link_error","data":{"record_id":"1"}}' localhost:5000/events
```

The `time` field above is for boardless Play-mode UI testing. A `status: "play"` event with `time` means the turntable is spinning; any other status means it is not spinning. This does not change real board event production.

An NFC reading error appears only before the first successful tag scan. Later read failures leave the last resolved record or Record Not Found view visible in Standby. NFC polling pauses during Playing; an externally supplied null scan event leaves Playing uninterrupted.

## Utils

### Stylus hours

The local database at `data/now-spinning.db` holds each stylus's total usage.
Use Python 3's built-in SQLite support to display, set, or reset it from the
project directory; these commands do not need a running server or the app's
Python dependencies.

**Keep the app stopped while using this tool. It has no application lock.**
Running it during playback can let pending, unsaved usage change the total
you specify. Follow this procedure on the Pi:

1. Exit the app through its normal **Exit** control so pending usage is saved.
2. Wait until the app has stopped.
3. List saved styli to find the ID:
   ```bash
   ./bin/stylus-hours list
   ```
4. Replace stylus `1`'s total with `97.3` hours, or reset it to zero:
   ```bash
   ./bin/stylus-hours set 1 97.3
   # Or, to reset:
   ./bin/stylus-hours reset 1
   ```
5. Start the app with `./bin/run_kiosk.sh`. It will load the saved total.

`set` replaces the total; it does not add hours. Each successful change displays
the previous and new totals, for example:

```text
Stylus 1: 102.4 hours -> 97.3 hours
```

Hours must be finite and zero or more. A missing database or stylus, invalid
hours, or a failed save produces an error and a nonzero exit status. The tool
does not create a database or missing stylus.

On a new Pi, sync the collection first, then stop the app
and use `set` to enter the initial total before restarting.

### NFC

To read NFC tag:
```bash
python -m exp.nfc.nfc_read
```

To write NFC tag:
```bash
python -m exp.nfc.nfc_write
```

To diagnose NFC card type:
```bash
python -m exp.nfc.nfc_diagnose
```

To debug PN532 module (UART):
```bash
python -m exp.nfc.nfc_debug_uart
```
or (I2C)
```bash
python -m exp.nfc.nfc_debug_i2c
```

### Calibration

To check IR sensor and get RPM treshold:
```bash
python -m exp.platter_spinning
```

To calibrate platter spinning detection and tonearm delay in milliseconds, run
on the Raspberry Pi with the platter sensor connected:
```bash
python -m exp.spinning_detection_calibration
```

To test stopped detection with the same sensor sampling loop, start with the
platter spinning, run:
```bash
python -m exp.spinning_detection_calibration --mode stop
```
Then stop the platter. The script prints each measured RPM sample and exits
after stopped detection triggers.

For my **Dual 721** constants are the next:
- `TONEARM_DELAY_AUTO = AVG(12171, 13868, 11240, 12434, 11512, 11683, 11896, 11719) = 12065`

## TODOs:
1. Stylus prev/next buttons - saving current selected stylus.
2. Played albums log with duration, and script to get results.
