import glob
import json
import os
import shutil


def extract_data(repo_dir):
    styli = []
    records = []

    styli_path = os.path.join(repo_dir, "data", "styli.json")
    if os.path.isfile(styli_path):
        with open(styli_path, "r") as f:
            styli = json.load(f)

    collection_path = os.path.join(repo_dir, "data", "collection.json")
    if os.path.isfile(collection_path):
        with open(collection_path, "r") as f:
            collection = json.load(f)

        for entry in collection:
            album_file = os.path.join(repo_dir, "albums", entry.get("album_file", ""))
            if os.path.isfile(album_file):
                with open(album_file, "r") as f:
                    album_data = json.load(f)
                record = {
                    "id": str(entry.get("id", "")),
                    "release_id": str(entry.get("release_id", "")),
                    "master_id": str(entry.get("master_id", "")),
                    "title": album_data.get("title", ""),
                    "artist": album_data.get("artist", ""),
                    "sides": album_data.get("sides", []),
                }
                records.append(record)

    return styli, records


def copy_images(repo_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for src in glob.glob(os.path.join(repo_dir, "images", "*.jpeg")):
        shutil.copy2(src, dest_dir)
