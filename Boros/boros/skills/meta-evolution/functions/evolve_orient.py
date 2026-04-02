
import os, json, glob
def evolve_orient(params: dict, kernel=None) -> dict:
    """Survey scores and identify weakest skill categories. Returns orientation data."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"

    # Read high-water marks
    hw_file = os.path.join(boros_dir, "skills", "eval-bridge", "state", "high_water_marks.json")
    high_water = {}
    if os.path.exists(hw_file):
        with open(hw_file) as f:
            high_water = json.load(f)

    # Read latest eval scores
    results_dir = os.path.join(boros_dir, "eval-generator", "shared", "results")
    latest_scores = {}
    if os.path.isdir(results_dir):
        result_files = sorted(glob.glob(os.path.join(results_dir, "*.json")), key=os.path.getmtime, reverse=True)
        if result_files:
            try:
                with open(result_files[0]) as f:
                    latest_scores = json.load(f).get("scores", {})
            except Exception:
                pass

    # Read score history for trend
    score_file = os.path.join(boros_dir, "memory", "score_history.jsonl")
    history = []
    if os.path.exists(score_file):
        with open(score_file) as f:
            for line in f:
                if line.strip():
                    try:
                        history.append(json.loads(line))
                    except Exception:
                        pass

    # List all skill function files for targeting
    skills_dir = os.path.join(boros_dir, "skills")
    skill_targets = []
    if os.path.isdir(skills_dir):
        for skill_name in os.listdir(skills_dir):
            func_dir = os.path.join(skills_dir, skill_name, "functions")
            if os.path.isdir(func_dir):
                for py_file in glob.glob(os.path.join(func_dir, "*.py")):
                    if os.path.basename(py_file) != "__init__.py" and not py_file.endswith("__"):
                        # Check file size — small files are likely stubs
                        size = os.path.getsize(py_file)
                        if size < 150:
                            skill_targets.append({
                                "skill": skill_name,
                                "file": os.path.relpath(py_file, kernel.boros_root if kernel else "."),
                                "size_bytes": size,
                                "likely_stub": True
                            })

    # Sort by size (smallest = most stub-like)
    skill_targets.sort(key=lambda x: x["size_bytes"])

    return {
        "status": "ok",
        "high_water_marks": high_water,
        "latest_scores": latest_scores,
        "history_entries": len(history),
        "stub_functions": skill_targets[:10],
        "total_stubs": len(skill_targets),
        "recommendation": f"Found {len(skill_targets)} stub functions. Start with the smallest."
    }
