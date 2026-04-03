
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

    # Extract detailed feedback for the weakest category from recent eval results
    feedback = {"quality_reason": "Not provided", "outcome_details": "No specific failures logged"}
    if weakest_category and eval_results:
        latest = eval_results[-1]
        breakdown = latest.get("scoring_breakdown", {}).get(weakest_category, {})
        feedback["quality_reason"] = breakdown.get("quality_reason", feedback["quality_reason"])
        feedback["outcome_details"] = breakdown.get("outcome_details", feedback["outcome_details"])

    return {
        "status": "ok",
        "total_entries": len(entries),
        "analyzed": len(recent),
        "category_analysis": analysis,
        "weakest_category": weakest_category,
        "weakest_score": round(lowest_avg, 3),
        "recommendation": _generate_detailed_recommendation(weakest_category, lowest_avg, feedback) if weakest_category else "No score data available. Run evaluations first."
    }

def _generate_detailed_recommendation(category, score, feedback):
    reason = feedback.get("quality_reason", "No specific reason given")
    outcome = feedback.get("outcome_details", "No detailed outcomes logged")
    
    recommendation = (
        f"To improve '{category}' (avg: {score:.3f}), you must address actual evaluation failures.\n"
        f"Eval Sandbox Feedback: {reason}\n"
        f"Outcome Details: {outcome}\n\n"
    )

    if category == "reasoning_architecture":
        recommendation += (
            f"**Actionable Architectural Insights:**\n"
            f"- Consider reviewing the current flow of information between skills. Are there bottlenecks or inefficient data transfers?\n"
            f"- Evaluate the modularity and separation of concerns within the code. Can any components be more independent?\n"
            f"- Look for opportunities to introduce caching or optimize frequently accessed data structures.\n"
            f"- Ensure that error handling and recovery mechanisms are robust and well-defined.\n"
            f"- If outcome details were more granular, we could pinpoint exact code sections. Future evaluations should aim to log more specific failure points (e.g., line numbers, specific API calls that failed).\n\n"
        )
    
    recommendation += (
        f"Generate a hypothesis that makes CONCRETE logical and algorithmic improvements. Do NOT just change prompt strings or formatting. Look deeply at the underlying data structures, API interactions, or workflow constraints causing this failure."
    )
    
    return recommendation
