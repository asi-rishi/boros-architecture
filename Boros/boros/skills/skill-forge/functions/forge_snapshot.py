
import os, json, shutil, uuid, datetime
def forge_snapshot(params: dict, kernel=None) -> dict:
    """Create a restorable snapshot of a skill's current function files."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    skill_name = params.get("skill_name", "")
    if not skill_name:
        return {"status": "error", "message": "skill_name required"}

    func_dir = os.path.join(boros_dir, "skills", skill_name, "functions")
    if not os.path.isdir(func_dir):
        return {"status": "error", "message": f"Skill functions not found: {func_dir}"}

    snapshot_id = f"snap-{uuid.uuid4().hex[:8]}"
    snap_dir = os.path.join(boros_dir, "snapshots", snapshot_id)
    backup_dir = os.path.join(snap_dir, "functions_backup")
    os.makedirs(backup_dir, exist_ok=True)

    # Copy all .py files
    files_copied = []
    for fname in os.listdir(func_dir):
        if fname.endswith(".py"):
            shutil.copy2(os.path.join(func_dir, fname), os.path.join(backup_dir, fname))
            files_copied.append(fname)

    # Write metadata
    with open(os.path.join(snap_dir, "snapshot_meta.json"), "w") as f:
        json.dump({
            "snapshot_id": snapshot_id,
            "skill_name": skill_name,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "files": files_copied
        }, f, indent=2)

    return {"status": "ok", "snapshot_id": snapshot_id, "files_snapshotted": len(files_copied)}
