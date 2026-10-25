## Why

Stopping Python polling leaves the PN532 RF field powered, including during playback and other inactive modes. Bound detection and explicitly manage the field to reduce unnecessary RF activity while preserving responsive record identification.

## What Changes

- Add confirmed RF on/off control to both I2C and UART drivers, finite passive activation, monotonic shared command deadlines, and response command validation.
- Probe for at most 200 ms, with a 500 ms RF-off pause between attempts and after operations; retain 30-second interactive waits.
- Keep RF enabled through authentication and complete payload transfer, then disable it on every exit path and before closing connections.
- Keep inactive modes RF-off and serialize hardware operations in the NFC worker, allowing bounded in-flight work to clean up after a mode transition.
- Preserve public NFC signatures, payloads, boardless behavior, events, duplicate suppression, and last-record retention.
- Add fake transport/clock and mode lifecycle coverage, with a simple post-deployment end-to-end check.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `nfc-library`: RF lifecycle, bounded detection, response validation, cleanup, and explicit transport/RF errors.
- `mode-state-machine`: Standby detection timing, serialized mode transitions, and RF-off inactive modes and idle Link/Re-link.

## Impact

Both PN532 drivers, the hardware NFC backend, the NFC coordinator, and Python tests. No external API or dependency changes. After deployment, check normal scanning, linking, and mode changes through the app. The completed `keep-last-record-on-nfc-read-error` change remains separate and unarchived.
