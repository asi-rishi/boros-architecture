
import os, json
_scratchpad = {}
def scratchpad_write(params: dict, kernel=None) -> dict:
    _scratchpad[params.get("key", "")] = params.get("value", "")
    return {"status": "ok"}

def scratchpad_read(params: dict, kernel=None) -> dict:
    key = params.get("key", "")
    if key in _scratchpad:
        return {"status": "ok", "value": _scratchpad[key]}
    return {"status": "ok", "value": None, "message": f"Key '{key}' not found"}

def scratchpad_clear(params: dict, kernel=None) -> dict:
    key = params.get("key")
    if key:
        _scratchpad.pop(key, None)
    else:
        _scratchpad.clear()
    return {"status": "ok"}
