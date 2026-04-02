
import os, json, datetime
def loop_end_cycle(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    
    state_file = os.path.join(boros_dir, "session", "loop_state.json")
    if os.path.exists(state_file):
        with open(state_file) as f:
            state = json.load(f)
        cycle = state.get("cycle", 1)
        state["stage"] = None
        state["cycle_ended_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)
    else:
        cycle = 0

    # Clean up session artifacts (keep state files)
    session_dir = os.path.join(boros_dir, "session")
    keep = {"loop_state.json", "current_cycle.json"}
    if os.path.isdir(session_dir):
        for item in os.listdir(session_dir):
            if item not in keep and not os.path.isdir(os.path.join(session_dir, item)):
                try:
                    os.remove(os.path.join(session_dir, item))
                except: pass

    # Log
    log_file = os.path.join(boros_dir, "logs", "cycles.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(f"Cycle {cycle} ended at {datetime.datetime.utcnow().isoformat()}Z\n")

    return {"status": "ok", "cycle": cycle, "message": f"Cycle {cycle} complete."}
