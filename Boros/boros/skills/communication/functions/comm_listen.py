
import os, json
def comm_listen(params: dict, kernel=None) -> dict:
    """Check for pending director commands."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    pending_file = os.path.join(boros_dir, "commands", "pending.json")
    if os.path.exists(pending_file):
        with open(pending_file) as f:
            data = json.load(f)
        pending = data.get("pending", [])
        if pending:
            # Clear after reading
            with open(pending_file, "w") as f:
                json.dump({"pending": []}, f)
        return {"status": "ok", "messages": pending, "count": len(pending)}
    return {"status": "ok", "messages": [], "count": 0}
