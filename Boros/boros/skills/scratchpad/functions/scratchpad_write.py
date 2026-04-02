import os
import json

SCRATCHPAD_FILE = "memory/sessions/scratchpad.json"

def _load_scratchpad():
    if os.path.exists(SCRATCHPAD_FILE):
        with open(SCRATCHPAD_FILE, "r") as f:
            return json.load(f)
    return {}

def _save_scratchpad(data):
    os.makedirs(os.path.dirname(SCRATCHPAD_FILE), exist_ok=True)
    with open(SCRATCHPAD_FILE, "w") as f:
        json.dump(data, f)

def scratchpad_write(params: dict, kernel=None) -> dict:
    scratchpad_data = _load_scratchpad()
    key = params.get("key", "")
    value = params.get("value", "")
    scratchpad_data[key] = value
    _save_scratchpad(scratchpad_data)
    return {"status": "ok"}
