
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
                        size = os.path.getsize(py_file)
                        skill_targets.append({
                            "skill": skill_name,
                            "file": os.path.relpath(py_file, kernel.boros_root if kernel else "."),
                            "size_bytes": size,
                            "likely_stub": size < 150
                        })

    # Improve targeting logic (tunnel vision fix)
    recent_targets = []
    records_dir = os.path.join(boros_dir, "memory", "evolution_records")
    if os.path.isdir(records_dir):
        # Sort by mtime to get the most recent ones
        prop_files = sorted(glob.glob(os.path.join(records_dir, "prop-*.json")), key=os.path.getmtime, reverse=True)
        for rec in prop_files:
            try:
                with open(rec) as f:
                    prop = json.load(f)
                    target = prop.get("target_file", "").replace('\\', '/')
                    if target:
                        recent_targets.append(target)
            except:
                pass
    
    # Consider only the last 5 unique targets for extreme penalty
    recent_targets = list(dict.fromkeys(recent_targets))[:5]

    filtered_targets = []
    for target in skill_targets:
        file_path_norm = target["file"].replace('\\', '/')
        if any(rt and file_path_norm.endswith(rt.split('/')[-1]) for rt in recent_targets):
            continue # Complete filter out recently targeted files to force diversity
        
        # Priority score (lower is better)
        score = target["size_bytes"] / 1000.0  # Base score from size
        target["priority_score"] = score
        filtered_targets.append(target)

    if not filtered_targets:
        # Fallback if somehow EVERYTHING was recently targeted
        filtered_targets = skill_targets

    # Sort by priority score
    filtered_targets.sort(key=lambda x: x["priority_score"])
    
    import random
    # Select from bottom 20% to force mutation diversity
    candidates = filtered_targets[:max(5, len(filtered_targets) // 5)]
    random.shuffle(candidates)

    return {
        "status": "ok",
        "high_water_marks": high_water,
        "latest_scores": latest_scores,
        "history_entries": len(history),
        "stub_functions": candidates[:10],
        "total_stubs": len(skill_targets),
        "recommendation": f"Found {len(skill_targets)} candidate files. Target one of the identified files to diversify evolutionary scope."
    }
