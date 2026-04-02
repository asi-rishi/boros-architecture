import json

def reason_decompose(params: dict, kernel=None) -> dict:
    problem = params.get("problem", "")
    if not problem:
        return {"status": "error", "message": "problem required"}
        
    if kernel and hasattr(kernel, "evolution_llm"):
        prompt = (f"Decompose the following problem into a logical sequence of sub-problems or steps.\n"
                  f"Problem: {problem}\n\n"
                  f"Respond ONLY with a valid JSON array of strings: [\"step 1\", \"step 2\"]")
        try:
            res = kernel.evolution_llm.complete([{"role": "user", "content": prompt}], system="You are the reasoning cortex. Decompose the problem.")
            text = "".join(b.get("text", "") for b in res.get("content", []) if b.get("type") == "text")
            import re
            match = re.search(r'\[.*\]', text, flags=re.DOTALL)
            if match:
                sub_problems = json.loads(match.group())
                return {"status": "ok", "sub_problems": sub_problems, "count": len(sub_problems)}
        except Exception as e:
            return {"status": "error", "message": f"LLM decomposition failed: {e}"}
            
    # Fallback
    parts = [s.strip() for s in problem.split(".") if s.strip()]
    return {"status": "ok", "sub_problems": parts, "count": len(parts), "note": "Heuristic fallback."}
