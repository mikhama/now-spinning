import json
import os
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy
from unittest.mock import mock_open, patch

import api.main as api_main
from api.main import app, build_initial_events, is_boardless_mode, runtime_state
from api.services.db import database


class LinkingApiTestCase(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        self.original_runtime_state = deepcopy(runtime_state)
        self.original_temperature_publisher_started = api_main.temperature_publisher_started
        database.DB_PATH = os.path.join(self.tmpdir.name, "now-spinning.db")
        database.init_db()
        self.client = app.test_client()

    def tearDown(self):
        database.DB_PATH = self.original_db_path
        runtime_state.clear()
        runtime_state.update(self.original_runtime_state)
        api_main.temperature_publisher_started = self.original_temperature_publisher_started
        self.tmpdir.cleanup()

    def insert_record(self, record_id="1", linked=0):
        conn = database._get_connection()
        try:
            conn.execute(
                "INSERT INTO record (id, release_id, master_id, title, artist, sides, linked) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (record_id, "release-" + record_id, "master-" + record_id, "Title", "Artist", json.dumps([]), linked),
            )
            conn.commit()
        finally:
            conn.close()

    def get_linked_value(self, record_id="1"):
        conn = database._get_connection()
        try:
            row = conn.execute("SELECT linked FROM record WHERE id = ?", (record_id,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def insert_stylus(self, stylus_id="1", distance_hours=89.6):
        conn = database._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO stylus (id, name, distance_hours, capacity_min_hours, capacity_max_hours, active)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (stylus_id, "Stylus " + stylus_id, distance_hours, 500, 1000, 1),
            )
            conn.commit()
        finally:
            conn.close()

    def get_stylus_hours(self, stylus_id="1"):
        conn = database._get_connection()
        try:
            row = conn.execute("SELECT distance_hours FROM stylus WHERE id = ?", (stylus_id,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def test_mark_record_linked_reports_updated_rows(self):
        self.insert_record("1", linked=0)

        self.assertTrue(database.mark_record_linked("1"))
        self.assertEqual(self.get_linked_value("1"), 1)
        self.assertFalse(database.mark_record_linked("999"))

    def test_records_link_endpoint_persists_or_returns_404(self):
        self.insert_record("1", linked=0)

        response = self.client.post("/records/1/link")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        self.assertEqual(self.get_linked_value("1"), 1)

        missing_response = self.client.post("/records/999/link")
        self.assertEqual(missing_response.status_code, 404)

    def test_stylus_reset_endpoint_persists_zero_hours(self):
        self.insert_stylus("1", distance_hours=89.6)

        response = self.client.post("/styli/1/reset")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        self.assertEqual(self.get_stylus_hours("1"), 0)
        self.assertEqual(runtime_state["stylus_hours"]["1"], 0)

    def test_styli_endpoint_reads_persisted_hours_after_reset(self):
        self.insert_stylus("1", distance_hours=89.6)

        self.client.post("/styli/1/reset")
        response = self.client.get("/styli")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()[0]["hours"], 0)

    def test_initial_events_do_not_emit_default_stylus_hours(self):
        runtime_state["stylus_hours"] = {}

        events = build_initial_events()

        self.assertFalse(any(event["event"] == "stylus_hours" for event in events))

    def test_initial_events_emit_null_temperature_until_real_reading_exists(self):
        runtime_state["temperature_c"] = None

        events = build_initial_events()

        temperature_events = [event for event in events if event["event"] == "temperature_c"]
        self.assertEqual(temperature_events, [{"event": "temperature_c", "data": {"temp_c": None}}])
        self.assertNotEqual(temperature_events[0]["data"]["temp_c"], 59)

    def test_initial_events_emit_real_temperature_after_reading_exists(self):
        runtime_state["temperature_c"] = 59.2

        events = build_initial_events()

        self.assertIn({"event": "temperature_c", "data": {"temp_c": 59.2}}, events)

    def test_temperature_endpoint_is_removed(self):
        response = self.client.get("/temperature")

        self.assertEqual(response.status_code, 404)

    def test_read_pi_temperature_returns_celsius_or_none(self):
        with patch("builtins.open", mock_open(read_data="59200\n")):
            self.assertEqual(api_main.read_pi_temperature_c(), 59.2)

        with patch("builtins.open", side_effect=FileNotFoundError("missing")):
            self.assertIsNone(api_main.read_pi_temperature_c())

    def test_temperature_publisher_broadcasts_successful_payload_without_waiting(self):
        sent_messages = []

        message = api_main.publish_temperature_once(
            read_temperature=lambda: 59.2,
            broadcast=sent_messages.append,
        )

        expected = {"event": "temperature_c", "data": {"temp_c": 59.2}}
        self.assertEqual(message, expected)
        self.assertEqual(sent_messages, [expected])

    def test_temperature_publisher_broadcasts_null_payload_without_waiting(self):
        sent_messages = []

        message = api_main.publish_temperature_once(
            read_temperature=lambda: None,
            broadcast=sent_messages.append,
        )

        expected = {"event": "temperature_c", "data": {"temp_c": None}}
        self.assertEqual(message, expected)
        self.assertEqual(sent_messages, [expected])

    def test_temperature_publisher_starts_once_per_process(self):
        api_main.temperature_publisher_started = False

        with patch("api.main.threading.Thread") as thread_class:
            self.assertTrue(api_main.start_temperature_publisher())
            self.assertFalse(api_main.start_temperature_publisher())

        thread_class.assert_called_once()
        thread_class.return_value.start.assert_called_once()

    def test_frontend_does_not_fetch_temperature_endpoint(self):
        app_js = Path(__file__).resolve().parents[1] / "ui" / "app.js"
        source = app_js.read_text()

        self.assertNotIn('fetch("/temperature")', source)
        self.assertIn('case "temperature_c":', source)

    def test_stylus_reset_endpoint_returns_404_without_changing_data(self):
        self.insert_stylus("1", distance_hours=89.6)

        response = self.client.post("/styli/999/reset")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json(), {"error": "Not found"})
        self.assertEqual(self.get_stylus_hours("1"), 89.6)

    def test_link_success_event_validates_persists_then_broadcasts(self):
        self.insert_record("1", linked=0)
        payload = {"event": "link_success", "data": {"record_id": "1"}}

        with patch("api.main.broadcast_message") as broadcast_message:
            response = self.client.post("/events", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        self.assertEqual(self.get_linked_value("1"), 1)
        broadcast_message.assert_called_once_with(payload)

    def test_link_success_event_rejects_missing_or_unknown_record_id(self):
        with patch("api.main.broadcast_message") as broadcast_message:
            missing_response = self.client.post("/events", json={"event": "link_success", "data": {}})
            unknown_response = self.client.post(
                "/events",
                json={"event": "link_success", "data": {"record_id": "999"}},
            )

        self.assertEqual(missing_response.status_code, 400)
        self.assertEqual(unknown_response.status_code, 404)
        broadcast_message.assert_not_called()

    def test_link_error_event_is_broadcast(self):
        payload = {"event": "link_error", "data": {"record_id": "1"}}

        with patch("api.main.broadcast_message") as broadcast_message:
            response = self.client.post("/events", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        broadcast_message.assert_called_once_with(payload)

    def test_boardless_mode_helper_matches_true_case_insensitively(self):
        for value in ("true", "TRUE", "TrUe"):
            with patch.dict(os.environ, {"BOARDLESS_MODE": value}):
                self.assertTrue(is_boardless_mode())

        for value in ("", "false", "1", " true "):
            with patch.dict(os.environ, {"BOARDLESS_MODE": value}, clear=False):
                self.assertFalse(is_boardless_mode())

    def test_index_leaves_html_unmarked_without_boardless_mode(self):
        with patch.dict(os.environ, {}, clear=True):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<html lang="en">', html)
        self.assertNotIn("data-boardless-mode", html)

    def test_index_marks_html_in_boardless_mode(self):
        with patch.dict(os.environ, {"BOARDLESS_MODE": "TRUE"}):
            response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<html data-boardless-mode="true" lang="en">', html)

    def test_kiosk_exit_rejects_when_shutdown_not_enabled(self):
        with patch.dict(os.environ, {}, clear=True):
            with patch("api.main.threading.Timer") as timer:
                response = self.client.post("/kiosk/exit")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.get_json(), {"error": "Kiosk shutdown is disabled"})
        timer.assert_not_called()

    def test_kiosk_exit_schedules_parent_termination_when_enabled(self):
        with patch.dict(os.environ, {"KIOSK_SHUTDOWN_ENABLED": "TRUE"}):
            with patch("api.main.threading.Timer") as timer:
                response = self.client.post("/kiosk/exit")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"success": True})
        timer.assert_called_once()
        delay, callback = timer.call_args.args
        self.assertEqual(delay, 0.1)
        self.assertEqual(callback.__name__, "terminate_kiosk_runner")
        timer.return_value.start.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
