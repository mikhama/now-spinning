"""Exercise both real driver implementations with scheduled wire-level replies."""

import sys
import unittest
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from drv.pn532 import PN532Commands
from lib.nfc import NfcError, NfcNoCard, Pn532Backend
from api.nfc_coordinator import NfcCoordinator

# Optional hardware packages are not needed for the fake transports.
with patch.dict(sys.modules, {
    "serial": SimpleNamespace(Serial=None),
    "smbus2": SimpleNamespace(SMBus=None, i2c_msg=None),
}):
    from drv.pn532_i2c import PN532 as I2C
    from drv.pn532_uart import PN532 as UART


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []
        self.on_sleep = lambda seconds: None

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.on_sleep(seconds)
        self.sleeps.append(seconds)
        self.now += seconds


def reply(command, payload=b""):
    return PN532Commands()._build_frame(bytes([0xd5, command + 1]) + payload)


CARD = b"\x01\x01\x00\x04\x00\x04\x01\x02\x03\x04"


class Wire:
    def __init__(self, clock):
        self.clock = clock
        self.frames = []
        self.commands = []
        self.rf = None
        self.closed = False
        self.handler = self.normal_reply

    def normal_reply(self, command, params):
        payload = b"\x00" if command == 0x4a else b""
        return [(0, PN532Commands._ACK), (0.01, reply(command, payload))]

    def write(self, frame):
        if frame.startswith(b"\x55"):
            return len(frame)
        command, params = frame[6], bytes(frame[7:-2])
        self.commands.append((self.clock.now, command, params))
        if command == 0x32 and params[:1] == b"\x01":
            self.rf = bool(params[1])
        for delay, packet in self.handler(command, params):
            self.frames.append((self.clock.now + delay, packet))
        self.frames.sort(key=lambda item: item[0])
        return len(frame)

    def ready(self):
        return bool(self.frames and self.frames[0][0] <= self.clock.now)

    def close(self):
        self.closed = True


class SerialWire(Wire):
    def reset_input_buffer(self):
        self.frames.clear()

    def reset_output_buffer(self):
        pass

    @property
    def in_waiting(self):
        return len(self.frames[0][1]) if self.ready() else 0

    def read(self, count):
        return self.frames.pop(0)[1]


class Message:
    def __init__(self, data=None, count=0):
        self.data = data
        self.count = count

    def __bytes__(self):
        return self.data


class I2cWire(Wire):
    def __init__(self, clock):
        super().__init__(clock)
        self.read_sizes = []

    def i2c_rdwr(self, message):
        if message.count == 0:
            self.write(message.data)
        elif message.count == 1:
            message.data = bytes([int(self.ready())])
        else:
            self.read_sizes.append(message.count)
            packet = self.frames.pop(0)[1] if self.ready() else b""
            if packet == PN532Commands._ACK and message.count > len(packet) + 1:
                raise TimeoutError(110, "I2C read exceeds the available ACK frame")
            message.data = b"\x01" + packet[:message.count - 1].ljust(message.count - 1, b"\x00")


class DriverTestCase(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.enterContext(patch("time.monotonic", self.clock.monotonic))
        self.enterContext(patch("time.sleep", self.clock.sleep))
        self.enterContext(patch("time.time", side_effect=AssertionError("Use monotonic time")))

    def driver(self, kind, *, initialize=True):
        if kind == "uart":
            wire = SerialWire(self.clock)
            constructor = self.enterContext(patch("drv.pn532_uart.serial.Serial", return_value=wire))
            if initialize:
                driver = UART()
                self.assertEqual(constructor.call_args.kwargs["timeout"], 0)
            else:
                driver = UART.__new__(UART)
                driver.ser = wire
        else:
            wire = I2cWire(self.clock)
            self.enterContext(patch("drv.pn532_i2c.SMBus", return_value=wire))
            self.enterContext(patch("drv.pn532_i2c.i2c_msg", SimpleNamespace(
                write=lambda address, data: Message(data=bytes(data)),
                read=lambda address, count: Message(count=count),
            )))
            if initialize:
                driver = I2C()
            else:
                driver = I2C.__new__(I2C)
                driver.address, driver.bus = 0x24, wire
        return driver, wire

    def test_initialization_and_explicit_rf_command_bytes(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                self.assertEqual([(cmd, args) for _, cmd, args in wire.commands], [
                    (0x14, b"\x01" if kind == "uart" else b"\x01\x14\x01"),
                    (0x32, b"\x05\xff\x01\x00"), (0x32, b"\x01\x00"),
                ])
                self.assertFalse(wire.rf)
                self.assertTrue(driver.set_rf_field(True))
                self.assertTrue(driver.set_rf_field(False))
                self.assertEqual([args for _, _, args in wire.commands[-2:]], [b"\x01\x01", b"\x01\x00"])

    def test_i2c_startup_reads_ack_separately(self):
        driver, wire = self.driver("i2c")
        self.assertFalse(wire.rf)
        # One status byte plus the six-byte ACK, then the response buffer.
        self.assertEqual(wire.read_sizes, [7, 65, 7, 65, 7, 65])
        driver.set_rf_field(True)
        driver.set_rf_field(False)
        self.assertEqual(wire.read_sizes[-4:], [7, 65, 7, 65])

    def test_i2c_startup_retries_temporary_ready_poll_errors(self):
        for error_number in (5, 110):
            with self.subTest(errno=error_number):
                driver, wire = self.driver("i2c", initialize=False)
                original_transfer = wire.i2c_rdwr
                failed_polls = set()
                wire.handler = lambda cmd, args: (
                    [(0, driver._ACK), (0.01, reply(cmd, b"\x32\x01\x06\x07"))]
                    if cmd == driver.CMD_FIRMWARE_VERSION else wire.normal_reply(cmd, args))

                def transfer(message):
                    if message.count == 1:
                        key = (len(wire.commands), wire.frames[0][1])
                        if key not in failed_polls:
                            failed_polls.add(key)
                            self.clock.now += 0.002
                            raise OSError(error_number, "temporarily busy")
                    original_transfer(message)

                with patch.object(wire, "i2c_rdwr", side_effect=transfer):
                    driver._initialize()
                    self.assertFalse(wire.rf)
                    self.assertFalse(wire.closed)
                    self.assertEqual(driver.get_firmware_version(), {
                        "ic": 0x32, "ver": 1, "rev": 6, "support": 7,
                    })
                    driver.close()
                self.assertEqual(len(failed_polls), 10)
                self.assertFalse(wire.rf)
                self.assertTrue(wire.closed)

    def test_i2c_persistent_poll_errors_keep_shared_deadline_and_original_errno(self):
        driver, wire = self.driver("i2c")
        original_transfer = wire.i2c_rdwr
        failure = TimeoutError(110, "status unavailable")
        polls = []

        def transfer(message):
            if message.count == 1:
                polls.append(self.clock.now)
                self.clock.now += 0.002
                raise failure
            original_transfer(message)

        start = self.clock.now
        with patch.object(wire, "i2c_rdwr", side_effect=transfer):
            with self.assertRaisesRegex(NfcError, "ready-status read.*110") as raised:
                driver.send_command(0x4a, b"\x01\x00", timeout=0.035)
        self.assertGreater(len(polls), 1)
        self.assertAlmostEqual(self.clock.now - start, 0.035)
        self.assertIs(raised.exception.__cause__.__cause__, failure)

    def test_i2c_busy_frame_status_is_retried_during_startup_and_firmware_read(self):
        driver, wire = self.driver("i2c", initialize=False)
        original_transfer = wire.i2c_rdwr
        busy_frames = set()
        wire.handler = lambda cmd, args: (
            [(0, driver._ACK), (0.01, reply(cmd, b"\x32\x01\x06\x07"))]
            if cmd == driver.CMD_FIRMWARE_VERSION else wire.normal_reply(cmd, args))

        def transfer(message):
            if message.count > 1:
                key = (len(wire.commands), wire.frames[0][1])
                if key not in busy_frames:
                    busy_frames.add(key)
                    message.data = bytes(message.count)
                    return
            original_transfer(message)

        with patch.object(wire, "i2c_rdwr", side_effect=transfer):
            driver._initialize()
            self.assertEqual(driver.get_firmware_version()["ic"], 0x32)
            driver.close()
        self.assertEqual(len(busy_frames), 10)
        self.assertFalse(wire.rf)
        self.assertTrue(wire.closed)

    def test_i2c_persistent_busy_frame_status_uses_existing_deadline(self):
        driver, wire = self.driver("i2c")
        original_transfer = wire.i2c_rdwr

        def transfer(message):
            if message.count > 1:
                message.data = bytes(message.count)
            else:
                original_transfer(message)

        start = self.clock.now
        with patch.object(wire, "i2c_rdwr", side_effect=transfer):
            with self.assertRaisesRegex(NfcError, "timed out"):
                driver.send_command(0x4a, b"\x01\x00", timeout=0.035)
        self.assertAlmostEqual(self.clock.now - start, 0.035)

    def test_i2c_transfer_errors_identify_stage_and_do_not_retry_frame_transfers(self):
        for stage, expected in (("write", "command write"), ("ack", "ACK read"),
                                ("response", "response read")):
            with self.subTest(stage=stage):
                driver, wire = self.driver("i2c")
                original_transfer = wire.i2c_rdwr
                failures = []

                def transfer(message):
                    if ((stage == "write" and message.count == 0)
                            or (stage == "ack" and message.count == 7)
                            or (stage == "response" and message.count == 65)):
                        failures.append(message)
                        raise TimeoutError(110, "transfer timed out")
                    original_transfer(message)

                with patch.object(wire, "i2c_rdwr", side_effect=transfer):
                    with self.assertRaisesRegex(NfcError, expected):
                        driver.send_command(0x14, b"\x01\x14\x01")
                self.assertEqual(len(failures), 1)

    def test_startup_cleanup_failure_reports_initial_error_too(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind, initialize=False)
                initial_error = NfcError("SAM handshake timed out")
                wire.handler = lambda cmd, args: (_ for _ in ()).throw(OSError("bus timed out"))
                with patch.object(driver, "_wakeup", side_effect=initial_error):
                    with self.assertRaisesRegex(NfcError, "SAM handshake timed out.*RF-off failed") as raised:
                        driver._initialize()
                self.assertIs(raised.exception.__cause__, initial_error)
                self.assertTrue(wire.closed)

    def test_delayed_response_after_ack_and_fragmented_uart_reply(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                response = reply(0x32)
                wire.handler = lambda cmd, args: [
                    (0.01, driver._ACK),
                    *([(0.12, response[:5]), (0.15, response[5:])] if kind == "uart"
                      else [(0.15, response)]),
                ]
                start = self.clock.now
                self.assertEqual(driver.send_command(0x32, b"\x01\x00", timeout=0.2), b"")
                self.assertGreaterEqual(self.clock.now - start, 0.15)

    def test_ack_and_response_share_budget(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                wire.handler = lambda cmd, args: [(0.15, driver._ACK), (0.25, reply(cmd, b"\x00"))]
                start = self.clock.now
                with self.assertRaises(NfcError):
                    driver.send_command(0x4a, b"\x01\x00", timeout=10)
                self.assertAlmostEqual(self.clock.now - start, 0.2)

    def test_caller_timeout_caps_budget(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                wire.handler = lambda cmd, args: [(0, driver._ACK)]
                start = self.clock.now
                with self.assertRaises(NfcError):
                    driver.send_command(0x4a, b"\x01\x00", timeout=0.035)
                self.assertAlmostEqual(self.clock.now - start, 0.035)

    def test_slow_status_check_cannot_start_more_io_or_sleep_after_deadline(self):
        for kind in ("uart", "i2c"):
            for ready in (False, True):
                with self.subTest(kind=kind, ready=ready):
                    driver, wire = self.driver(kind)
                    start = self.clock.now
                    sleep_count = len(self.clock.sleeps)
                    reads = []

                    if kind == "uart":
                        def slow_status():
                            self.clock.now += 0.05
                            return 6 if ready else 0

                        status_patch = patch.object(SerialWire, "in_waiting", new_callable=PropertyMock,
                                                    side_effect=slow_status)
                        read_patch = patch.object(wire, "read", wraps=wire.read)
                    else:
                        original_transfer = wire.i2c_rdwr

                        def slow_status(message):
                            if message.count:
                                reads.append(message.count)
                                self.clock.now += 0.05
                                message.data = bytes([int(ready)])
                            else:
                                original_transfer(message)

                        status_patch = patch.object(wire, "i2c_rdwr", side_effect=slow_status)
                        read_patch = nullcontext(None)

                    with status_patch, read_patch as read:
                        with self.assertRaises(NfcError):
                            driver.send_command(0x4a, b"\x01\x00", timeout=0.035)
                        if read is not None:
                            read.assert_not_called()
                    if kind == "i2c":
                        self.assertEqual(reads, [1])
                    self.assertEqual(self.clock.sleeps[sleep_count:], [])
                    self.assertAlmostEqual(self.clock.now - start, 0.05)

    def test_probe_budget_includes_time_spent_enabling_rf(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                wire.handler = lambda cmd, args: (
                    [(0.01, driver._ACK), (0.05, reply(cmd, b"\x00"))] if cmd == 0x4a
                    else wire.normal_reply(cmd, args))
                start = self.clock.now
                with self.assertRaises(NfcError):
                    driver.read_passive_target(timeout=0.04)
                detection = next(when for when, cmd, _ in wire.commands if cmd == 0x4a)
                cleanup = wire.commands[-1][0]
                self.assertGreater(detection, start)
                self.assertAlmostEqual(cleanup - start, 0.04)
                self.assertFalse(wire.rf)

    def test_rf_on_failure_never_starts_detection_and_still_attempts_off(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                wire.commands.clear()
                wire.handler = lambda cmd, args: ([(0, driver._ACK), (0.01, reply(cmd, b"bad"))]
                                                if args == b"\x01\x01" else wire.normal_reply(cmd, args))
                with self.assertRaisesRegex(NfcError, "RF-on"):
                    driver.read_passive_target()
                self.assertEqual([(cmd, args) for _, cmd, args in wire.commands], [
                    (0x32, b"\x01\x01"), (0x32, b"\x01\x00")])
                self.assertFalse(wire.rf)

    def test_stale_responses_are_rejected_before_and_after_ack(self):
        for kind in ("uart", "i2c"):
            for expected_arrives in (False, True):
                with self.subTest(kind=kind, expected_arrives=expected_arrives):
                    driver, wire = self.driver(kind)
                    # Even a matching response before the command ACK is stale.
                    wire.handler = lambda cmd, args: [
                        (0, reply(cmd, b"old")), (0.01, driver._ACK),
                        (0.02, reply(0x02, b"stale")),
                        *([(0.05, reply(cmd))] if expected_arrives else []),
                    ]
                    if expected_arrives:
                        self.assertTrue(driver.set_rf_field(False))
                    else:
                        with self.assertRaises(NfcError):
                            driver.send_command(0x32, timeout=0.1)

    def test_malformed_frames_are_errors(self):
        valid = reply(0x4a, b"\x00")
        bad_frames = [b"garbage", valid[:4] + b"\x00" + valid[5:],
                      valid[:-2] + b"\xff\x00", valid[:-1] + b"\xff",
                      PN532Commands()._build_frame(b"\xd4\x4b\x00"), valid[:6]]
        for kind in ("uart", "i2c"):
            for packet in bad_frames:
                with self.subTest(kind=kind, packet=packet):
                    driver, wire = self.driver(kind)
                    wire.handler = lambda cmd, args: [(0, driver._ACK), (0.01, packet)]
                    with self.assertRaises(NfcError) as raised:
                        driver.send_command(0x4a, timeout=0.2)
                    self.assertNotIsInstance(raised.exception, NfcNoCard)

    def test_missing_ack_or_response_is_not_absence(self):
        for kind in ("uart", "i2c"):
            for packets in ([], [(0, PN532Commands._ACK)], [(0, reply(0x4a, b"\x00"))]):
                with self.subTest(kind=kind, packets=packets):
                    driver, wire = self.driver(kind)
                    wire.handler = lambda cmd, args: packets if cmd == 0x4a else wire.normal_reply(cmd, args)
                    with self.assertRaises(NfcError) as raised:
                        driver.read_passive_target(timeout=0.1)
                    self.assertNotIsInstance(raised.exception, NfcNoCard)
                    self.assertFalse(wire.rf)

    def test_zero_targets_is_absence_but_malformed_targets_are_errors(self):
        for kind in ("uart", "i2c"):
            for payload in (b"\x00", b"", b"\x00\x00", CARD[:-1], CARD[:5] + b"\xff" + CARD[6:]):
                with self.subTest(kind=kind, payload=payload):
                    driver, wire = self.driver(kind)
                    wire.handler = lambda cmd, args: (
                        [(0, driver._ACK), (0.01, reply(cmd, payload))] if cmd == 0x4a
                        else wire.normal_reply(cmd, args))
                    if payload == b"\x00":
                        self.assertIsNone(driver.read_passive_target())
                    else:
                        with self.assertRaises(NfcError):
                            driver.read_passive_target()
                    self.assertFalse(wire.rf)

    def test_no_card_waits_have_half_second_rf_off_pauses(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                def check_pause(seconds):
                    if seconds > 0.01:
                        self.assertFalse(wire.rf)
                self.clock.on_sleep = check_pause
                start = self.clock.now
                self.assertIsNone(driver.wait_for_card(timeout=3))
                probes = [when for when, cmd, _ in wire.commands if cmd == 0x4a]
                self.assertEqual(len(probes), 6)
                self.assertTrue(all(b - a >= 0.5 for a, b in zip(probes, probes[1:])))
                self.assertGreaterEqual(self.clock.sleeps.count(0.5), 5)
                self.assertAlmostEqual(self.clock.now - start, 3)
                self.assertFalse(wire.rf)

    def test_write_keeps_30_second_detection_limit_and_off_pauses(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                backend = Pn532Backend.__new__(Pn532Backend)
                backend._nfc = driver
                self.clock.on_sleep = lambda seconds: self.assertFalse(wire.rf) if seconds > 0.01 else None
                start = self.clock.now
                with self.assertRaises(NfcError):
                    backend.write("1")
                self.assertAlmostEqual(self.clock.now - start, 30, delta=0.03)
                probes = [when for when, cmd, _ in wire.commands if cmd == 0x4a]
                self.assertGreater(len(probes), 40)
                self.assertTrue(all(b - a >= 0.5 for a, b in zip(probes, probes[1:])))
                self.assertFalse(wire.rf)

    def test_found_card_retains_rf_for_payload(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                wire.handler = lambda cmd, args: ([(0, driver._ACK), (0.01, reply(cmd, CARD))]
                                                if cmd == 0x4a else wire.normal_reply(cmd, args))
                card = driver.wait_for_card()
                self.assertEqual(card["uid"], b"\x01\x02\x03\x04")
                self.assertTrue(wire.rf)
                driver.close()
                self.assertFalse(wire.rf)
                self.assertTrue(wire.closed)

    def test_transport_errors_are_nfc_errors_and_cleanup_closes(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                wire.handler = lambda cmd, args: (_ for _ in ()).throw(OSError("unplugged"))
                with self.assertRaisesRegex(NfcError, "transport failed"):
                    driver.get_firmware_version()
                with self.assertRaisesRegex(NfcError, "RF-off failed"):
                    driver.close()
                self.assertTrue(wire.closed)

    def test_initialization_failure_attempts_rf_off_and_closes(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind, initialize=False)
                wire.handler = lambda cmd, args: [(0, driver._ACK), (0.01, reply(cmd, b"bad"))]
                with self.assertRaises(NfcError):
                    driver._initialize()
                self.assertEqual(wire.commands[-1][1:], (0x32, b"\x01\x00"))
                self.assertTrue(wire.closed)

    def test_rf_failures_and_cleanup_preserve_original_exception(self):
        for kind in ("uart", "i2c"):
            with self.subTest(kind=kind):
                driver, wire = self.driver(kind)
                def fail(cmd, args):
                    if cmd == 0x4a:
                        raise OSError("detection broken")
                    if args == b"\x01\x00":
                        raise OSError("off broken")
                    return wire.normal_reply(cmd, args)
                wire.handler = fail
                with self.assertRaisesRegex(NfcError, "RF-off failed") as raised:
                    driver.read_passive_target()
                chain = []
                error = raised.exception
                while error is not None:
                    chain.append(str(error))
                    error = error.__context__
                self.assertTrue(any("detection broken" in value for value in chain))

    def backend_coordinator(self, driver):
        backend = Pn532Backend.__new__(Pn532Backend)
        backend._nfc = driver
        coordinator = NfcCoordinator(read_nfc=backend.read, write_nfc=backend.write)
        return coordinator

    def test_inactive_modes_stay_off_after_standby_and_during_idle(self):
        for kind in ("uart", "i2c"):
            for mode in ("play", "sync", "stylus", "link", "re-link", "unknown", None):
                with self.subTest(kind=kind, mode=mode):
                    driver, wire = self.driver(kind)
                    coordinator = self.backend_coordinator(driver)
                    coordinator.set_mode(mode)
                    count = len(wire.commands)
                    coordinator.tick()
                    self.assertEqual(len(wire.commands), count)
                    self.assertFalse(wire.rf)
                    coordinator.set_mode("standby")
                    coordinator.tick()
                    self.assertFalse(wire.rf)
                    count = len(wire.commands)
                    coordinator.set_mode(mode)
                    coordinator.tick()
                    coordinator.tick()
                    self.assertEqual(len(wire.commands), count)
                    self.assertFalse(wire.rf)

    def test_transition_during_probe_cleans_up_without_mode_handler_commands(self):
        for kind in ("uart", "i2c"):
            for mode in ("play", "sync", "stylus", "link", "re-link"):
                for result in ("absence", "success", "failure"):
                    with self.subTest(kind=kind, mode=mode, result=result):
                        driver, wire = self.driver(kind)
                        coordinator = self.backend_coordinator(driver)
                        messages = []
                        coordinator.broadcast = messages.append
                        def handler(cmd, args):
                            if cmd == 0x4a:
                                self.assertTrue(wire.rf)
                                count = len(wire.commands)
                                coordinator.set_mode(mode)
                                self.assertEqual(len(wire.commands), count)
                                if result == "failure":
                                    raise OSError("probe failed")
                                return [(0, driver._ACK), (0.01, reply(cmd, CARD if result == "success" else b"\x00"))]
                            if cmd == 0x40:
                                self.assertTrue(wire.rf)
                                return [(0, driver._ACK), (0.01, reply(cmd, b"\x00\x01a" + bytes(14)))]
                            return wire.normal_reply(cmd, args)
                        wire.handler = handler
                        coordinator.set_mode("standby")
                        coordinator.tick()
                        self.assertEqual(coordinator.current_mode, mode)
                        self.assertFalse(wire.rf)
                        self.assertEqual(messages, [])
                        count = len(wire.commands)
                        coordinator.tick()
                        self.assertEqual(len(wire.commands), count)

    def test_link_writes_require_request_and_keep_rf_through_every_page(self):
        for kind in ("uart", "i2c"):
            for mode in ("link", "re-link"):
                with self.subTest(kind=kind, mode=mode):
                    driver, wire = self.driver(kind)
                    coordinator = self.backend_coordinator(driver)
                    probes = []
                    def handler(cmd, args):
                        if cmd == 0x4a:
                            probes.append(self.clock.now)
                            payload = CARD if len(probes) == 3 else b"\x00"
                        elif cmd == 0x40:
                            self.assertTrue(wire.rf)
                            payload = b"\x00"
                        else:
                            return wire.normal_reply(cmd, args)
                        return [(0, driver._ACK), (0.01, reply(cmd, payload))]
                    wire.handler = handler
                    self.clock.on_sleep = lambda seconds: self.assertFalse(wire.rf) if seconds > 0.01 else None
                    coordinator.set_mode(mode)
                    count = len(wire.commands)
                    coordinator.tick()
                    self.assertEqual(len(wire.commands), count)
                    coordinator.request_write("abc-123", mode=mode)
                    coordinator.tick()
                    self.assertEqual(len(probes), 3)
                    self.assertTrue(all(b - a >= 0.5 for a, b in zip(probes, probes[1:])))
                    writes = [args for _, cmd, args in wire.commands if cmd == 0x40]
                    self.assertEqual(len(writes), 2)
                    self.assertEqual(b"".join(args[3:] for args in writes), b"\x07abc-123")
                    self.assertFalse(wire.rf)
                    count = len(wire.commands)
                    coordinator.tick()
                    self.assertEqual(len(wire.commands), count)

    def test_worker_sleeps_half_second_with_rf_off_after_each_outcome(self):
        for kind in ("uart", "i2c"):
            for outcome in ("absence", "success", "failure", "write"):
                with self.subTest(kind=kind, outcome=outcome):
                    driver, wire = self.driver(kind)
                    coordinator = self.backend_coordinator(driver)
                    def handler(cmd, args):
                        if cmd == 0x4a:
                            if outcome == "failure":
                                raise OSError("failed")
                            payload = b"\x00" if outcome == "absence" else CARD
                        elif cmd == 0x40:
                            self.assertTrue(wire.rf)
                            payload = b"\x00" if outcome == "write" else b"\x00\x01a" + bytes(14)
                        else:
                            return wire.normal_reply(cmd, args)
                        return [(0, driver._ACK), (0.01, reply(cmd, payload))]
                    wire.handler = handler
                    pauses = []
                    def sleep(seconds):
                        self.assertFalse(wire.rf)
                        pauses.append(seconds)
                        coordinator.stop()
                    coordinator.sleep = sleep
                    coordinator.set_mode("standby")
                    if outcome == "write":
                        coordinator.request_write("abc-123", mode="link")
                    coordinator.run_forever()
                    self.assertEqual(pauses, [0.5])


if __name__ == "__main__":
    unittest.main()
