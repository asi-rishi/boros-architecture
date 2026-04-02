
import os, json
def identity_read(params: dict, kernel=None) -> dict:
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    id_file = os.path.join(boros_dir, "skills", "identity", "state", "identity.json")
    if os.path.exists(id_file):
        with open(id_file) as f:
            return {"status": "ok", "identity": json.load(f)}
    return {"status": "ok", "identity": None, "message": "Identity missing, please configure."}
