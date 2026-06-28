## 1. Detector Core

- [x] 1.1 Create a backend playback status module with `SPINNING_RPM_THRESHOLD = 4500`, `TONEARM_DELAY_AUTO = 9726`, and `SAMPLE_INTERVAL_SECONDS = 1`.
- [x] 1.2 Implement a testable detector state machine for stopped, threshold-reached, and playing states.
- [x] 1.3 Emit a play message with zero-padded `MM:SS` time when RPM remains at or above the threshold until the tonearm delay elapses.
- [x] 1.4 Reset pending threshold timing without emitting play or stop when RPM falls below threshold before the tonearm delay elapses.
- [x] 1.5 Emit exactly one stop message when RPM falls below threshold after playback has started.
- [x] 1.6 Suppress duplicate play messages within the same elapsed second and duplicate stop messages while detected state remains unchanged.

## 2. RPM Reader and Publisher

- [x] 2.1 Add an RPM reader abstraction that can calculate RPM from the platter sensor using the existing GPIO pin and pulse-counting pattern.
- [x] 2.2 Keep GPIO imports and hardware setup lazy so non-Raspberry Pi environments can import and run the API server.
- [x] 2.3 Implement a playback status publisher loop that samples RPM every one second and feeds the detector.
- [x] 2.4 Ensure unavailable RPM hardware is logged and does not crash the API server process.

## 3. API Server Integration

- [x] 3.1 Wire detector output through `broadcast_message` using `{"event": "status", "data": {"status": "play", "time": "MM:SS"}}`.
- [x] 3.2 Wire detector output through `broadcast_message` using `{"event": "status", "data": {"status": "stop"}}`.
- [x] 3.3 Add a playback status publisher start-once guard and lock matching the existing temperature publisher pattern.
- [x] 3.4 Start the playback status publisher from the API server entry point alongside temperature publishing.
- [x] 3.5 Preserve existing boardless `/events` status publishing behavior.

## 4. Tests and Verification

- [x] 4.1 Add unit tests for below-threshold RPM samples producing no events.
- [x] 4.2 Add unit tests for threshold crossing, tonearm delay completion, and timed play event emission.
- [x] 4.3 Add unit tests for RPM dropping below threshold before delay completion resetting pending playback without events.
- [x] 4.4 Add unit tests for stop event emission after playback started.
- [x] 4.5 Add unit tests for play time updates, same-second duplicate suppression, and duplicate stop suppression.
- [x] 4.6 Add unit tests for playback publisher start-once behavior.
- [x] 4.7 Add or update API tests proving detected status messages update runtime state through the existing event format.
- [x] 4.8 Run the backend test suite.
