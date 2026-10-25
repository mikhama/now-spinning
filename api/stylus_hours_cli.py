"""Offline stylus-hour commands; requires only the Python standard library."""

import argparse
import sqlite3
import sys

from api.services.db import database


OFFLINE_USAGE = (
    "Exit the app normally and wait until it has stopped. Run list, then set or "
    "reset an ID, then restart the app. This tool has no application lock: "
    "pending playback usage can change your specified total if the app is running. "
    "On a new Pi, sync the collection first, then stop the app and set initial hours."
)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="stylus-hours",
        description="Display, set, or reset saved stylus hours in data/now-spinning.db.",
        epilog=OFFLINE_USAGE,
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List each stylus ID, name, and saved hours", epilog=OFFLINE_USAGE)
    set_parser = commands.add_parser("set", help="Replace a stylus's total hours", epilog=OFFLINE_USAGE)
    set_parser.add_argument("id", help="Stylus ID from list")
    set_parser.add_argument("hours", help="Finite total hours, zero or more")
    reset_parser = commands.add_parser("reset", help="Set a stylus's total hours to zero", epilog=OFFLINE_USAGE)
    reset_parser.add_argument("id", help="Stylus ID from list")
    args = parser.parse_args(argv)

    try:
        if args.command == "list":
            styli = database.get_all_styli(existing_only=True)
            if not styli:
                print("No styli found. Sync the collection first.")
            else:
                print("ID\tName\tHours")
                for stylus in styli:
                    print(f"{stylus['id']}\t{stylus['name']}\t{stylus['hours']}")
        else:
            hours = args.hours if args.command == "set" else 0
            result = database.set_stylus_hours(args.id, hours)
            if result is None:
                raise ValueError(f"Stylus {args.id} does not exist")
            previous_hours, new_hours = result
            print(f"Stylus {args.id}: {previous_hours} hours -> {new_hours} hours")
    except (OSError, sqlite3.Error, ValueError) as error:
        print(f"Error: {error} (database: {database.DB_PATH})", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
