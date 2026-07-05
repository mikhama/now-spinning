## Context

`api/main.py` currently starts the temperature publisher, playback status publisher, NFC coordinator, and Flask server directly in the `__main__` block. The playback status publisher creates its GPIO RPM reader inside the background thread and logs initialization failures without failing the process. The NFC backend is also lazy and is first initialized when NFC read/write code asks for the backend. This means hardware wiring or permission problems can surface only after the script appears to have started successfully.

The requested behavior is hardware-mode fail-fast startup: if both required sensors are not ready and working at the beginning of startup, the script must raise an error and exit instead of running in a degraded state.

## Goals / Non-Goals

**Goals:**

- Validate NFC and RPM playback sensors before starting background workers or Flask in hardware mode.
- Raise a clear startup error when either sensor is unavailable or fails its readiness probe.
- Keep boardless mode usable on development machines without physical hardware.
- Reuse the same sensor initialization paths as runtime workers so readiness checks exercise the real dependencies.

**Non-Goals:**

- No change to HTTP or WebSocket API payloads.
- No change to RPM classification thresholds or NFC scan/write behavior.
- No long-running calibration or interactive NFC card detection during startup.

## Decisions

1. Add a startup orchestration function in `api/main.py`.

   The entry point should call a single function that installs shutdown hooks, runs sensor readiness checks, starts workers, and then starts Flask. This makes the startup order testable without invoking `app.run` directly.

   Alternative considered: keep logic inline in `if __name__ == "__main__"`. That would work but makes startup failure ordering harder to test.

2. Treat boardless mode as exempt from hardware readiness.

   `BOARDLESS_MODE=true` is the established development mode for running without hardware. The readiness check should return successfully without probing physical NFC or GPIO sensors in that mode.

   Alternative considered: probe boardless backends. That would risk blocking on simulated input and would not validate physical hardware.

3. Split sensor readiness into small injectable helpers.

   NFC readiness should force the NFC backend to initialize without waiting for a card. RPM readiness should create the GPIO RPM reader, perform an initial `read_rpm()` sample, and close the reader before returning. Tests can inject fakes to verify success and failure paths.

   Alternative considered: start the existing workers and observe whether they fail. That preserves the current late-failure behavior and does not meet the fail-fast requirement.

4. Let startup failures propagate as exceptions.

   Readiness failures should raise a purpose-specific runtime error with sensor context. The top-level script does not swallow it, so `python -m api.main` exits non-zero and service managers can report the failure.

   Alternative considered: log and continue. That conflicts with the requested behavior.

## Risks / Trade-offs

- Hardware readiness probes may briefly open and close the same devices that workers open again -> Keep probes short, close readers explicitly, and reuse existing initialization paths.
- NFC backend initialization may prove the PN532 is reachable but not that a card is present -> The startup requirement is sensor readiness, not card availability; startup must not block waiting for media.
- Existing tests may assume missing RPM hardware is non-fatal -> Update tests and specs to distinguish hardware mode from boardless mode.
