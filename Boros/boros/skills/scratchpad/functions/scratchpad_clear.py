import os
import json
from .scratchpad_write import SCRATCHPAD_FILE, _load_scratchpad, _save_scratchpad

def scratchpad_clear(params: dict, kernel=None) -> dict:
    scratchpad_data = _load_scratchpad()
    key = params.get("key")
    if key:
        scratchpad_data.pop(key, None)
    else:
        scratchpad_data.clear()
    _save_scratchpad(scratchpad_data)
    return {"status": "ok"}