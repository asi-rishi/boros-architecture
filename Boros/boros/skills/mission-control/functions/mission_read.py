
import os, json, uuid, datetime
def mission_read(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    queue = []
    for subdir in ["queue", "active", "completed"]:
        d = os.path.join(boros_dir, "tasks", subdir)
        if os.path.isdir(d):
            for f in os.listdir(d):
                if f.endswith(".json"):
                    try:
                        with open(os.path.join(d, f)) as fh:
                            task = json.load(fh)
                            task["_status"] = subdir
                            queue.append(task)
                    except: pass
    return {"status": "ok", "tasks": queue, "count": len(queue)}
