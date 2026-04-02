
import os, json, glob
def reflection_analyze_trace(params: dict, kernel=None) -> dict:
    """Analyze score history to identify trends, weaknesses, and opportunities."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    last_n = params.get("last_n_cycles", 5)

    # Read score history
    score_file = os.path.join(boros_dir, "memory", "score_history.jsonl")
    entries = []
    if os.path.exists(score_file):
        with open(score_file, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
    recent = entries[-last_n:] if entries else []

    # Read eval results directory
    results_dir = os.path.join(boros_dir, "eval-generator", "shared", "results")
    eval_results = []
    if os.path.isdir(results_dir):
        for rf in sorted(glob.glob(os.path.join(results_dir, "*.json")))[-last_n:]:
            try:
                with open(rf) as f:
                    eval_results.append(json.load(f))
            except Exception:
                pass

    # Aggregate scores by category
    category_scores = {}
    for entry in recent + eval_results:
        scores = entry.get("scores", entry)
        if isinstance(scores, dict):
            for cat, score in scores.items():
                if isinstance(score, (int, float)):
                    if cat not in category_scores:
                        category_scores[cat] = []
                    category_scores[cat].append(score)

    # Calculate averages and trends
    analysis = {}
    weakest_category = None
    lowest_avg = 1.0
    for cat, scores in category_scores.items():
        avg = sum(scores) / len(scores) if scores else 0
        trend = "stable"
        if len(scores) >= 2:
            if scores[-1] > scores[0]:
                trend = "improving"
            elif scores[-1] < scores[0]:
                trend = "declining"
        analysis[cat] = {"average": round(avg, 3), "trend": trend, "samples": len(scores), "latest": scores[-1] if scores else 0}
        if avg < lowest_avg:
            lowest_avg = avg
            weakest_category = cat

    return {
        "status": "ok",
        "total_entries": len(entries),
        "analyzed": len(recent),
        "category_analysis": analysis,
        "weakest_category": weakest_category,
        "weakest_score": round(lowest_avg, 3),
        "recommendation": f"To improve '{weakest_category}' (avg: {lowest_avg:.3f}), focus on refining the interpretation of architectural scores. Specifically, analyze why certain architectural choices led to lower scores and use these insights to generate more precise and actionable hypotheses for the next evolution cycle." if weakest_category else "No score data available. Run evaluations first."
    }
