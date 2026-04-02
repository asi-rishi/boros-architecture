
import datetime
def time_elapsed_since(params: dict, kernel=None) -> dict:
    ts = params.get("timestamp", "")
    if not ts:
        return {"status": "error", "message": "timestamp required"}
    try:
        then = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
        now = datetime.datetime.now(datetime.timezone.utc)
        elapsed = (now - then).total_seconds()
        return {"status": "ok", "elapsed_seconds": elapsed, "elapsed_minutes": round(elapsed / 60, 2)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
