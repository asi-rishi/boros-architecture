
import os, json, datetime
def time_estimate_remaining(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    max_minutes = kernel.config.get("max_cycle_duration_minutes", 10) if kernel else 10
    state_file = os.path.join(boros_dir, "skills", "loop-orchestrator", "state", "loop_state.json")
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
        started = state.get("cycle_started_at")
        if started:
            try:
                then = datetime.datetime.fromisoformat(started.replace("Z", "+00:00"))
                now = datetime.datetime.now(datetime.timezone.utc)
                elapsed = (now - then).total_seconds() / 60
                remaining = max(0, max_minutes - elapsed)
                return {"status": "ok", "remaining_minutes": round(remaining, 2), "elapsed_minutes": round(elapsed, 2)}
            except: pass
    return {"status": "ok", "remaining_minutes": max_minutes, "elapsed_minutes": 0}
