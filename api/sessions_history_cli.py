"""Committed playback history commands using only the Python standard library."""

import argparse
from datetime import datetime
import sqlite3
import sys
import unicodedata

from api.services.db import database


CONFIRMATION = "yes I hereby confirm"
USAGE = (
    "The default report shows saved history only and may run while the app runs. "
    "Before clear, exit the app normally and wait until it has stopped; restart afterward. "
    "Clear has no application lock. Neither command creates a missing database or upgrades "
    "its schema; start the updated app first. Collection sync preserves history. "
    "Playback before this feature cannot be reconstructed. Album ID is the local record.id."
)


def combine_sessions(entries):
    combined = []
    for entry in entries:
        if combined and combined[-1]["record_id"] == entry["record_id"]:
            combined[-1]["session_duration_sec"] += entry["session_duration_sec"]
        else:
            combined.append(dict(entry))
    return combined


def format_duration(seconds):
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def display_width(value):
    return sum(0 if unicodedata.combining(c) else 2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in value)


def _text(value, fallback="Unknown"):
    return " ".join(str(value).split()) if value else fallback


def render_report(entries, *, local_timezone=None):
    rows = [["Started at", "Duration", "Artist", "Album", "Album ID"]]
    for entry in combine_sessions(entries):
        started = datetime.fromisoformat(entry["session_started_at"])
        if started.tzinfo is None:
            raise ValueError("History timestamp is missing a UTC offset")
        rows.append([
            started.astimezone(local_timezone).isoformat(sep=" ", timespec="seconds"),
            format_duration(entry["session_duration_sec"]),
            _text(entry["artist"]),
            _text(entry["album"]),
            _text(entry["record_id"]),
        ])
    widths = [max(display_width(row[column]) for row in rows) for column in range(5)]
    return "\n".join(
        "  ".join(value + " " * (widths[column] - display_width(value)) for column, value in enumerate(row)).rstrip()
        for row in rows
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="sessions-history",
        description="Report saved playback sessions in data/now-spinning.db, combining consecutive entries for each album.",
        epilog=USAGE,
    )
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("clear", help="Clear only saved history after exact confirmation", epilog=USAGE)
    args = parser.parse_args(argv)

    try:
        if args.command == "clear":
            print("Exit the app normally and wait until it has stopped before clearing history.")
            response = input(f'Type exactly "{CONFIRMATION}" to delete saved playback history: ')
            if response != CONFIRMATION:
                print("Cancelled. History was not cleared.")
                return 0
            database.clear_playback_sessions()
            print("Playback history cleared.")
        else:
            entries = database.get_playback_sessions()
            print(render_report(entries))
            if not entries:
                print("No saved playback history.")
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        return 0
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Error: {error} (database: {database.DB_PATH})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
