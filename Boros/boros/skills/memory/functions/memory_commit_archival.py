
import os, json, uuid, datetime
def memory_commit_archival(params: dict, kernel=None) -> dict:
    """Commit an entry to long-term archival memory."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    entry = {
        "id": f"exp-{uuid.uuid4().hex[:8]}",
        "type": params.get("entry_type", "observation"),
        "content": params.get("content", ""),
        "tags": params.get("tags", []),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    exp_dir = os.path.join(boros_dir, "memory", "experiences")
    os.makedirs(exp_dir, exist_ok=True)
    with open(os.path.join(exp_dir, f"{entry['id']}.json"), "w") as f:
        json.dump(entry, f, indent=2)
    return {"status": "ok", "entry_id": entry["id"]}
