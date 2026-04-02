import os
import json
from .scratchpad_write import SCRATCHPAD_FILE, _load_scratchpad, _save_scratchpad

def scratchpad_read(params: dict, kernel=None) -> dict:
    scratchpad_data = _load_scratchpad()
    key = params.get("key", "")
    value = scratchpad_data.get(key)
    if value is not None:
        return {"status": "ok", "value": value}
    return {"status": "ok", "value": None, "message": f"Key '{key}' not found"}