
import os, json, uuid, datetime
def mission_queue_task(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    task_id = f"task-{uuid.uuid4().hex[:8]}"
    task = {"id": task_id, "description": params.get("description", ""), "priority": params.get("priority", "medium"), "created_at": datetime.datetime.utcnow().isoformat() + "Z"}
    queue_dir = os.path.join(boros_dir, "tasks", "queue")
    os.makedirs(queue_dir, exist_ok=True)
    with open(os.path.join(queue_dir, f"{task_id}.json"), "w") as f:
        json.dump(task, f, indent=2)
    return {"status": "ok", "task_id": task_id}
