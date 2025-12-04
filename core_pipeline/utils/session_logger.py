import json
import os
from datetime import datetime

BASE = "/home/ubuntu/garimpo-ml/gpt_exchange"

SESSION_LOG_PATH = f"{BASE}/SESSION_LOG.json"
CONTEXT_BOOT_PATH = f"{BASE}/CONTEXT_BOOT.json"


def now():
    return datetime.utcnow().isoformat() + "Z"


def init_session():
    data = {
        "session_id": now(),
        "timestamp_start": now(),
        "timestamp_end": "",
        "steps": []
    }
    with open(SESSION_LOG_PATH, "w") as f:
        json.dump(data, f, indent=4)


def append_step(step: dict):
    if not os.path.exists(SESSION_LOG_PATH):
        init_session()

    with open(SESSION_LOG_PATH, "r") as f:
        data = json.load(f)

    data["steps"].append(step)

    with open(SESSION_LOG_PATH, "w") as f:
        json.dump(data, f, indent=4)


def end_session():
    if not os.path.exists(SESSION_LOG_PATH):
        return

    with open(SESSION_LOG_PATH, "r") as f:
        data = json.load(f)

    data["timestamp_end"] = now()

    with open(SESSION_LOG_PATH, "w") as f:
        json.dump(data, f, indent=4)

    generate_context_boot(data)


def generate_context_boot(session_log: dict):
    context = {
        "last_session_id": session_log["session_id"],
        "timestamp": now(),
        "summary": "",
        "changed_files": [],
        "errors_fixed": [],
        "pending": [],
        "impact_map": [],
        "notes": ""
    }

    for step in session_log["steps"]:
        if step.get("file") and step["file"] not in context["changed_files"]:
            context["changed_files"].append(step["file"])

        if step["action"] == "fix_error":
            context["errors_fixed"].append(f"{step['error']} / {step['file']}")

    with open(CONTEXT_BOOT_PATH, "w") as f:
        json.dump(context, f, indent=4)
