"""Run real application cleanup with a simulated reader in a child process."""

from pathlib import Path
import atexit
import os
import signal
import sys
import threading
import time

import api.main as api_main
from drv.pn532 import PN532Commands
import lib.nfc as nfc_module


log_path = Path(sys.argv[1])
tag_present = sys.argv[2] == "present"
scenario = sys.argv[3]
reading = threading.Event()


def record(event):
    with log_path.open("a") as log:
        log.write(event + "\n")


class Reader(PN532Commands):
    def wait_for_card(self, timeout):
        record("read-start")
        reading.set()
        if scenario == "blocked":
            while True:
                time.sleep(0.05)
        while not api_main.nfc_coordinator.shutting_down:
            time.sleep(0.005)
        # Send repeated signals while the first handler waits for this read.
        if scenario == "signal":
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.02)
            os.kill(os.getpid(), signal.SIGINT)
        time.sleep(0.05)
        record("read-end")
        return {"uid": b"1234"} if tag_present else None

    def identify_card(self, card):
        return "ntag_ultralight"

    def ntag_read(self, page):
        return b"\x011" + bytes(14)

    def set_rf_field(self, enabled):
        if threading.current_thread() is not api_main.nfc_coordinator_thread:
            raise AssertionError("Hardware command outside the NFC worker")
        record("rf-off")
        return True

    def _close_connection(self):
        record("transport-close")


backend = nfc_module.Pn532Backend.__new__(nfc_module.Pn532Backend)
backend._nfc = Reader()
nfc_module._backend = backend
api_main.flush_pending_stylus_usage = lambda: record("stylus-flush")
api_main.nfc_coordinator.set_mode("standby")


def serve():
    while True:
        time.sleep(0.05)


if scenario == "atexit":
    atexit.register(lambda: record("process-exit"))
    api_main.install_shutdown_hooks()
    api_main.start_nfc_coordinator()
    if not reading.wait(2):
        raise RuntimeError("Read did not start")
else:
    try:
        api_main.start_api_server(
            verify_sensors=lambda: None, start_temperature=lambda: None,
            start_playback=lambda: None, run_flask=serve,
        )
    finally:
        record("process-exit")
