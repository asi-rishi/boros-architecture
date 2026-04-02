
import os, json
def identity_update(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    id_file = os.path.join(boros_dir, "skills", "identity", "state", "identity.json")
    os.makedirs(os.path.dirname(id_file), exist_ok=True)
    identity = {}
    if os.path.exists(id_file):
        with open(id_file) as f:
            identity = json.load(f)
    updates = params.get("updates", {})
    identity.update(updates)
    with open(id_file, "w") as f:
        json.dump(identity, f, indent=2)
    return {"status": "ok", "identity": identity}
