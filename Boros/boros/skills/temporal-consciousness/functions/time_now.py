
import datetime
def time_now(params: dict, kernel=None) -> dict:
    return {"status": "ok", "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}
