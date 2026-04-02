
import os, json
def time_cycle_started(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    state_file = os.path.join(boros_dir, "skills", "loop-orchestrator", "state", "loop_state.json")
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
        return {"status": "ok", "cycle_started_at": state.get("cycle_started_at")}
    return {"status": "ok", "cycle_started_at": None}
