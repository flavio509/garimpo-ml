import os
import json
import hashlib
from datetime import datetime

BASE_DIR = "/home/ubuntu/garimpo-ml"
MONITORED_DIRS = [
    f"{BASE_DIR}/core_pipeline",
    f"{BASE_DIR}/agent_pre_catalog",
    f"{BASE_DIR}/upload_manager"
]

SNAPSHOT_BEFORE = f"{BASE_DIR}/gpt_exchange/SERVER_SNAPSHOT_BEFORE.json"
SNAPSHOT_AFTER = f"{BASE_DIR}/gpt_exchange/SERVER_SNAPSHOT_AFTER.json"
SERVER_DIFF = f"{BASE_DIR}/gpt_exchange/SERVER_FILE_DIFF.json"


def file_hash(path):
    try:
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except:
        return None


def take_snapshot(save_path):
    snapshot = {}

    for folder in MONITORED_DIRS:
        for root, dirs, files in os.walk(folder):
            for file in files:
                full = os.path.join(root, file)
                snapshot[full] = {
                    "mtime": os.path.getmtime(full),
                    "size": os.path.getsize(full),
                    "hash": file_hash(full)
                }

    with open(save_path, "w") as f:
        json.dump(snapshot, f, indent=4)

    return snapshot


def compare_snapshots():
    with open(SNAPSHOT_BEFORE, "r") as f:
        before = json.load(f)

    with open(SNAPSHOT_AFTER, "r") as f:
        after = json.load(f)

    diff = {
        "modified": [],
        "created": [],
        "deleted": []
    }

    for path in after:
        if path not in before:
            diff["created"].append(path)
        else:
            if before[path]["hash"] != after[path]["hash"]:
                diff["modified"].append(path)

    for path in before:
        if path not in after:
            diff["deleted"].append(path)

    with open(SERVER_DIFF, "w") as f:
        json.dump(diff, f, indent=4)

    return diff
