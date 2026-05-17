import glob
import json
import logging
import os
import shutil

logger = logging.getLogger(__name__)


def extract_data(repo_dir):
    styli = []
    records = []

    styli_path = os.path.join(repo_dir, "data", "styli.json")
    if not os.path.isfile(styli_path):
        raise FileNotFoundError("Styli file not found: %s" % styli_path)
    with open(styli_path, "r") as f:
        styli = json.load(f)
    logger.info("Loaded %d styli from %s", len(styli), styli_path)

    collection_path = os.path.join(repo_dir, "data", "collection.json")
    if not os.path.isfile(collection_path):
        raise FileNotFoundError("Collection file not found: %s" % collection_path)
    with open(collection_path, "r") as f:
        collection = json.load(f)
    logger.info("Found %d entries in collection.json", len(collection))

    missing = []
    for entry in collection:
        release_id = str(entry.get("release_id", ""))
        album_file = os.path.join(repo_dir, "data", "albums", release_id + ".json")
        if not os.path.isfile(album_file):
            missing.append(album_file)
            continue
        with open(album_file, "r") as f:
            album_data = json.load(f)
        record = {
            "id": str(int(entry.get("id", "0"))),
            "release_id": str(entry.get("release_id", "")),
            "master_id": str(entry.get("master_id", "")),
            "title": album_data.get("title", ""),
            "artist": album_data.get("artist", ""),
            "sides": album_data.get("sides", []),
        }
        records.append(record)

    if missing:
        raise FileNotFoundError("%d/%d album files missing, first: %s" % (len(missing), len(collection), missing[0]))

    logger.info("Extracted %d records", len(records))

    return styli, records


def copy_images(repo_dir, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    for src in glob.glob(os.path.join(repo_dir, "images", "*.jpeg")):
        shutil.copy2(src, dest_dir)
