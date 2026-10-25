import threading

from lib.nfc import NfcError, NfcNoCard, close_backend, nfc_read_once, nfc_write


STANDBY_MODE = "standby"


class NfcShuttingDown(RuntimeError):
    pass


class NfcCoordinator:
    def __init__(
        self,
        *,
        read_nfc=nfc_read_once,
        write_nfc=nfc_write,
        close_nfc=close_backend,
        broadcast=None,
        persist_link_success=None,
        logger=None,
        poll_interval_seconds=0.5,
        read_timeout_seconds=0.2,
    ):
        self.read_nfc = read_nfc
        self.write_nfc = write_nfc
        self.close_nfc = close_nfc
        self.broadcast = broadcast
        self.persist_link_success = persist_link_success
        self.logger = logger
        self.poll_interval_seconds = poll_interval_seconds
        self.read_timeout_seconds = read_timeout_seconds
        self.current_mode = None
        self.last_successful_record_id = None
        self.last_emitted_record_id = None
        self.scan_error_emitted = False
        self.active_write_request = None
        self.cleanup_succeeded = None
        self._lock = threading.Lock()
        self._operation_lock = threading.Lock()
        self._stop_event = threading.Event()

    def set_mode(self, mode):
        with self._lock:
            self._check_accepting_work()
            previous_mode = self.current_mode
            self.current_mode = STANDBY_MODE if mode == STANDBY_MODE else mode
            if previous_mode != self.current_mode:
                self._log_info("NFC mode changed: %s -> %s", previous_mode, self.current_mode)

    def request_write(self, record_id, mode=None):
        if not record_id:
            raise ValueError("record_id is required")
        with self._lock:
            self._check_accepting_work()
            self.active_write_request = {
                "record_id": str(record_id),
                "mode": mode,
            }
            self._log_info("NFC write queued (record_id=%s, mode=%s)", record_id, mode)

    @property
    def shutting_down(self):
        return self._stop_event.is_set()

    def _check_accepting_work(self):
        if self._stop_event.is_set():
            raise NfcShuttingDown("NFC is shutting down")

    def stop(self):
        with self._lock:
            if not self._stop_event.is_set():
                self._log_info("NFC shutdown requested; discard queued work")
            self._stop_event.set()
            self.active_write_request = None

    def run_forever(self):
        self._log_info("NFC worker started")
        try:
            while not self._stop_event.is_set():
                self.tick()
                self._stop_event.wait(self.poll_interval_seconds)
        finally:
            self.stop()
            self._log_info("NFC reader cleanup started")
            try:
                self.close_nfc()
            except Exception as error:
                self.cleanup_succeeded = False
                self._log_error("NFC reader cleanup failed: %s", error)
            else:
                self.cleanup_succeeded = True
                self._log_info("NFC reader cleanup succeeded")
            self._log_info("NFC worker stopped")

    def tick(self):
        # Claim an operation under the state lock. Let an active operation finish.
        with self._operation_lock:
            with self._lock:
                if self._stop_event.is_set():
                    return
                request = dict(self.active_write_request) if self.active_write_request else None
                scan = request is None and self.current_mode == STANDBY_MODE
            if request is not None:
                self._process_write_request(request)
            elif scan:
                self._poll_standby_once()

    def _get_current_mode(self):
        with self._lock:
            return self.current_mode

    def _clear_active_write_request(self, request):
        with self._lock:
            if self.active_write_request == request:
                self.active_write_request = None

    def _poll_standby_once(self):
        try:
            self._log_info("NFC read attempt started (timeout=%s)", self.read_timeout_seconds)
            record_id = self.read_nfc(timeout=self.read_timeout_seconds)
        except NfcNoCard:
            self._log_info("NFC read completed: no card")
            return
        except NfcError as error:
            self._log_error("NFC read failed: %s", error)
            if self._get_current_mode() != STANDBY_MODE:
                return
            if self.last_successful_record_id is None and not self.scan_error_emitted:
                self._broadcast({"event": "scan", "data": {"record_id": None}})
                self.scan_error_emitted = True
            return

        self._log_info("NFC read succeeded (record_id=%s)", record_id)
        # Backend cleanup has completed. A late scan must not switch the UI
        # back to Standby after the user selected an inactive mode.
        if self._get_current_mode() != STANDBY_MODE:
            return
        record_id = str(record_id)
        self.last_successful_record_id = record_id
        self.scan_error_emitted = False
        if record_id != self.last_emitted_record_id:
            self._broadcast({"event": "scan", "data": {"record_id": record_id}})
            self.last_emitted_record_id = record_id

    def _process_write_request(self, request):
        record_id = request["record_id"]
        try:
            self._log_info("NFC write started (record_id=%s)", record_id)
            self.write_nfc(record_id)
        except NfcError as error:
            self._log_error("NFC write failed: %s", error)
            self._broadcast({"event": "link_error", "data": {"record_id": record_id}})
        else:
            self._log_info("NFC tag write confirmed (record_id=%s)", record_id)
            if self.persist_link_success and not self.persist_link_success(record_id):
                self._log_info("NFC link persistence failed (record_id=%s)", record_id)
                self._broadcast({"event": "link_error", "data": {"record_id": record_id}})
            else:
                self._broadcast({"event": "link_success", "data": {"record_id": record_id}})
                self._log_info("NFC write completed (record_id=%s)", record_id)
        finally:
            self._clear_active_write_request(request)

    def _broadcast(self, message):
        if self.broadcast:
            self.broadcast(message)

    def _log_error(self, message, error):
        if self.logger:
            self.logger.error(message, error, exc_info=True)

    def _log_info(self, message, *args):
        if self.logger:
            self.logger.info(message, *args)
