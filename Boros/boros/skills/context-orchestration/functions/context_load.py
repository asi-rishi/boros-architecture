
import os, json
def context_load(params: dict, kernel=None) -> dict:
    """Load fresh context at cycle start: identity, scores, hypothesis, recent experiences."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    manifest = {}

    # Load identity
    id_file = os.path.join(boros_dir, "skills", "identity", "state", "identity.json")
    if os.path.exists(id_file):
        with open(id_file) as f:
            manifest["identity"] = json.load(f)

    # Load recent scores
    score_file = os.path.join(boros_dir, "memory", "score_history.jsonl")
    if os.path.exists(score_file):
        with open(score_file) as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        manifest["recent_scores"] = [json.loads(l) for l in lines[-5:]] if lines else []

    # Load hypothesis if present
    hyp_file = os.path.join(boros_dir, "session", "hypothesis.json")
    if os.path.exists(hyp_file):
        with open(hyp_file) as f:
            manifest["hypothesis"] = json.load(f)

    # Load high-water marks
    hw_file = os.path.join(boros_dir, "skills", "eval-bridge", "state", "high_water_marks.json")
    if os.path.exists(hw_file):
        with open(hw_file) as f:
            manifest["high_water_marks"] = json.load(f)

    # Save context manifest
    os.makedirs(os.path.join(boros_dir, "session"), exist_ok=True)
    with open(os.path.join(boros_dir, "session", "context_manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return {"status": "ok", "loaded": True, "manifest_keys": list(manifest.keys()), "content": manifest}
