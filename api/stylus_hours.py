import threading


def parse_elapsed_seconds(time_value):
    if not isinstance(time_value, str):
        return None
    parts = time_value.split(":")
    if len(parts) != 2:
        return None
    try:
        minutes = int(parts[0])
        seconds = int(parts[1])
    except ValueError:
        return None
    if minutes < 0 or seconds < 0 or seconds > 59:
        return None
    return minutes * 60 + seconds


class StylusHoursTracker:
    def __init__(
        self,
        get_active_stylus,
        increment_stylus_hours,
        flush_interval_seconds=600,
    ):
        self.get_active_stylus = get_active_stylus
        self.increment_stylus_hours = increment_stylus_hours
        self.flush_interval_seconds = flush_interval_seconds
        self.lock = threading.RLock()
        self.active_stylus_id = None
        self.current_hours = None
        self.last_elapsed_seconds = None
        self.pending_seconds = 0

    def process_message(self, message):
        if message.get("event") != "status":
            return []

        data = message.get("data") or {}
        status = data.get("status")
        if status == "play":
            return self.process_play(data.get("time"))
        if status == "stop":
            self.flush_pending()
            with self.lock:
                self.last_elapsed_seconds = None
        return []

    def process_play(self, time_value):
        elapsed_seconds = parse_elapsed_seconds(time_value)
        if elapsed_seconds is None:
            return []

        with self.lock:
            was_tracking_stylus = self.active_stylus_id is not None
            if not self._ensure_active_stylus_locked():
                self.last_elapsed_seconds = elapsed_seconds
                return []

            if (
                not was_tracking_stylus
                or self.last_elapsed_seconds is None
                or elapsed_seconds < self.last_elapsed_seconds
            ):
                delta_seconds = 0
            else:
                delta_seconds = elapsed_seconds - self.last_elapsed_seconds

            self.last_elapsed_seconds = elapsed_seconds

            if delta_seconds <= 0:
                return []

            self.pending_seconds += delta_seconds
            self.current_hours += delta_seconds / 3600
            event = self._stylus_hours_event_locked()

        self.flush_periodic()
        return [event]

    def flush_periodic(self):
        with self.lock:
            flush_seconds = (self.pending_seconds // self.flush_interval_seconds) * self.flush_interval_seconds
        if flush_seconds > 0:
            self._flush_seconds(flush_seconds)

    def flush_pending(self):
        with self.lock:
            flush_seconds = self.pending_seconds
        if flush_seconds > 0:
            self._flush_seconds(flush_seconds)

    def reset_stylus(self, stylus_id):
        with self.lock:
            if self.active_stylus_id == str(stylus_id):
                self.current_hours = 0
                self.pending_seconds = 0
                self.last_elapsed_seconds = None

    def current_event(self):
        with self.lock:
            if self.active_stylus_id is None or self.current_hours is None:
                return None
            return self._stylus_hours_event_locked()

    def _flush_seconds(self, seconds):
        with self.lock:
            stylus_id = self.active_stylus_id
            seconds = min(seconds, self.pending_seconds)
        if stylus_id is None or seconds <= 0:
            return False

        updated = self.increment_stylus_hours(stylus_id, seconds / 3600)
        if not updated:
            return False

        with self.lock:
            if self.active_stylus_id == stylus_id:
                self.pending_seconds = max(0, self.pending_seconds - seconds)
        return True

    def _ensure_active_stylus_locked(self):
        if self.active_stylus_id is not None:
            return True

        stylus = self.get_active_stylus()
        if not stylus:
            return False

        self.active_stylus_id = str(stylus["id"])
        self.current_hours = float(stylus["hours"] or 0)
        return True

    def _stylus_hours_event_locked(self):
        return {
            "event": "stylus_hours",
            "data": {"stylus_id": self.active_stylus_id, "hours": self.current_hours},
        }
