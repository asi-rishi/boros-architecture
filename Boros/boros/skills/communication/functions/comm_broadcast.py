
import os, json, datetime
def comm_broadcast(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    message = params.get("message", "")
    channel = params.get("channel", "general")
    log_dir = os.path.join(boros_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    with open(os.path.join(log_dir, f"comm_{channel}.log"), "a") as f:
        f.write(f"[{datetime.datetime.utcnow().isoformat()}Z] {message}\n")
    return {"status": "ok", "channel": channel}
