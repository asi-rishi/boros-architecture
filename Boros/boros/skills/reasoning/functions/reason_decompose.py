
def reason_decompose(params: dict, kernel=None) -> dict:
    problem = params.get("problem", "")
    if not problem:
        return {"status": "error", "message": "problem required"}
    # Simple heuristic decomposition — LLM-level reasoning happens in the agent loop itself
    parts = [s.strip() for s in problem.split(".") if s.strip()]
    return {"status": "ok", "sub_problems": parts, "count": len(parts), "note": "Heuristic split. Use LLM reasoning for complex decomposition."}
