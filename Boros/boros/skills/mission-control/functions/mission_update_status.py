
import os, json, shutil
def mission_update_status(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    task_id = params.get("task_id", "")
    new_status = params.get("status", "completed")
    for subdir in ["queue", "active", "completed"]:
        fpath = os.path.join(boros_dir, "tasks", subdir, f"{task_id}.json")
        if os.path.exists(fpath):
            with open(fpath) as f:
                task = json.load(f)
            os.remove(fpath)
            dest_dir = os.path.join(boros_dir, "tasks", new_status)
            os.makedirs(dest_dir, exist_ok=True)
            task["status"] = new_status
            with open(os.path.join(dest_dir, f"{task_id}.json"), "w") as f:
                json.dump(task, f, indent=2)
            return {"status": "ok", "task_id": task_id, "new_status": new_status}
    return {"status": "error", "message": f"Task {task_id} not found"}
