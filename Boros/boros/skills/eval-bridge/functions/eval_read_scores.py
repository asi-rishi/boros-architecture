
import os, json, glob, time
def eval_read_scores(params: dict, kernel=None) -> dict:
    """Read evaluation scores from the eval-generator results directory."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    eval_id = params.get("eval_id", "")
    results_dir = os.path.join(boros_dir, "eval-generator", "shared", "results")

    if eval_id:
        # Read specific eval
        result_file = os.path.join(results_dir, f"{eval_id}.json")
        if os.path.exists(result_file):
            with open(result_file) as f:
                result = json.load(f)
            return {"status": "ok", "scores": result.get("scores", {}), "composite": result.get("composite", 0), "result": result}

    # Read latest results (poll briefly if no results yet)
    for attempt in range(3):
        if os.path.isdir(results_dir):
            result_files = sorted(glob.glob(os.path.join(results_dir, "*.json")), key=os.path.getmtime, reverse=True)
            if result_files:
                results = []
                for rf in result_files[:5]:
                    try:
                        with open(rf) as f:
                            results.append(json.load(f))
                    except Exception:
                        pass
                if results:
                    latest = results[0]
                    # Append to score history
                    score_hist = os.path.join(boros_dir, "memory", "score_history.jsonl")
                    os.makedirs(os.path.dirname(score_hist), exist_ok=True)
                    with open(score_hist, "a") as f:
                        f.write(json.dumps(latest.get("scores", {})) + "\n")
                    return {
                        "status": "ok",
                        "scores": latest.get("scores", {}),
                        "composite": latest.get("composite", 0),
                        "total_results": len(result_files),
                        "latest_eval_id": latest.get("eval_id", "")
                    }
        time.sleep(1)

    return {"status": "ok", "scores": {}, "composite": 0, "message": "No evaluation results found yet."}
