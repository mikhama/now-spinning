import threading
import time

from lib.nfc import NfcError, NfcNoCard, nfc_read_once, nfc_write


STANDBY_MODE = "standby"


class NfcCoordinator:
    def __init__(
        self,
        *,
        read_nfc=nfc_read_once,
        write_nfc=nfc_write,
        broadcast=None,
        persist_link_success=None,
        is_record_linked=None,
        logger=None,
        poll_interval_seconds=1,
        read_timeout_seconds=1,
        sleep=time.sleep,
    ):
        self.read_nfc = read_nfc
        self.write_nfc = write_nfc
        self.broadcast = broadcast
        self.persist_link_success = persist_link_success
        self.is_record_linked = is_record_linked
        self.logger = logger
        self.poll_interval_seconds = poll_interval_seconds
        self.read_timeout_seconds = read_timeout_seconds
        self.sleep = sleep
        self.current_mode = None
        self.last_successful_record_id = None
        self.last_emitted_record_id = None
        self.scan_error_emitted = False
        self.active_write_request = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def set_mode(self, mode):
        with self._lock:
            self.current_mode = STANDBY_MODE if mode == STANDBY_MODE else mode

    def request_write(self, record_id, mode=None):
        if not record_id:
            raise ValueError("record_id is required")
        with self._lock:
            self.active_write_request = {
                "record_id": str(record_id),
                "mode": mode,
            }

    def stop(self):
        self._stop_event.set()

    def run_forever(self):
        while not self._stop_event.is_set():
            self.tick()
            self.sleep(self.poll_interval_seconds)

    def tick(self):
        request = self._get_active_write_request()
        if request is not None:
            self._process_write_request(request)
            return

        if self._get_current_mode() == STANDBY_MODE:
            self._poll_standby_once()

    def _get_current_mode(self):
        with self._lock:
            return self.current_mode

    def _get_active_write_request(self):
        with self._lock:
            return dict(self.active_write_request) if self.active_write_request else None

    def _clear_active_write_request(self, request):
        with self._lock:
            if self.active_write_request == request:
                self.active_write_request = None

    def _poll_standby_once(self):
        try:
            record_id = self.read_nfc(timeout=self.read_timeout_seconds)
        except NfcNoCard:
            self.scan_error_emitted = False
            return
        except NfcError as error:
            self._log_error("NFC read failed: %s", error)
            if not self.scan_error_emitted:
                self._broadcast({"event": "scan", "data": {"record_id": None}})
                self.scan_error_emitted = True
            return

        record_id = str(record_id)
        if self.is_record_linked and not self.is_record_linked(record_id):
            self.scan_error_emitted = False
            self._broadcast({"event": "scan", "data": {"record_id": None}})
            return

        self.last_successful_record_id = record_id
        self.scan_error_emitted = False
        if record_id != self.last_emitted_record_id:
            self._broadcast({"event": "scan", "data": {"record_id": record_id}})
            self.last_emitted_record_id = record_id

    def _process_write_request(self, request):
        record_id = request["record_id"]
        try:
            self.write_nfc(record_id)
        except NfcError as error:
            self._log_error("NFC write failed: %s", error)
            self._broadcast({"event": "link_error", "data": {"record_id": record_id}})
        else:
            if self.persist_link_success and not self.persist_link_success(record_id):
                self._broadcast({"event": "link_error", "data": {"record_id": record_id}})
            else:
                self._broadcast({"event": "link_success", "data": {"record_id": record_id}})
        finally:
            self._clear_active_write_request(request)

    def _broadcast(self, message):
        if self.broadcast:
            self.broadcast(message)

    def _log_error(self, message, error):
        if self.logger:
            self.logger.error(message, error)
