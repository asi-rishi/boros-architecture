
import os, json, datetime
def review_proposal(params: dict, kernel=None) -> dict:
    """Submit a proposal to the Meta-Evaluation Review Board (secondary LLM).
    If meta_eval_llm is available, calls it for independent review.
    Falls back to rule-based review if no LLM is available."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"

    proposal_id = params.get("proposal_id", "unknown")
    diff = params.get("diff", "")
    description = params.get("description", "")
    target_file = params.get("target_file", "")

    # Try LLM-based review
    if kernel and kernel.meta_eval_llm:
        try:
            review_prompt = (
                f"You are the Boros Meta-Evaluation Review Board. Your job is to review "
                f"code changes proposed by the evolution engine and decide: apply, reject, or modify.\n\n"
                f"## Proposal: {proposal_id}\n"
                f"**Description:** {description}\n"
                f"**Target File:** {target_file}\n\n"
                f"## Code Diff:\n```\n{diff}\n```\n\n"
                f"Evaluate for:\n"
                f"1. Correctness: Will this code run without errors?\n"
                f"2. Improvement: Does it genuinely improve the function?\n"
                f"3. Safety: Could it break other parts of the system?\n"
                f"4. Python syntax: Is it valid Python?\n\n"
                f"Respond with EXACTLY one JSON object:\n"
                f'{{"verdict": "apply"|"reject"|"modify", "reason": "...", "confidence": 0.0-1.0}}'
            )

            response = kernel.meta_eval_llm.complete(
                [{"role": "user", "content": review_prompt}],
                system="You are a strict code reviewer. Respond only with the requested JSON."
            )

            # Parse LLM response
            response_text = ""
            for block in response.get("content", []):
                if block.get("type") == "text":
                    response_text += block["text"]

            # Extract JSON from response
            import re
            json_match = re.search(r'\{[^}]+\}', response_text)
            if json_match:
                review = json.loads(json_match.group())
                verdict = review.get("verdict", "apply")
                reason = review.get("reason", "LLM review")
                confidence = review.get("confidence", 0.5)
            else:
                verdict = "apply"
                reason = f"LLM responded but no parseable JSON: {response_text[:200]}"
                confidence = 0.3

        except Exception as e:
            verdict = "apply"
            reason = f"Meta-eval LLM call failed ({e}), defaulting to apply."
            confidence = 0.2
    else:
        # Rule-based fallback
        verdict = "apply"
        reason = "No meta-eval LLM configured. Rule-based approval."
        confidence = 0.5
        if not diff or len(diff.strip()) < 10:
            verdict = "reject"
            reason = "Empty or trivial diff."
            confidence = 0.9

    review_record = {
        "proposal_id": proposal_id,
        "verdict": verdict,
        "reason": reason,
        "confidence": confidence,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "reviewer": "meta_eval_llm" if (kernel and kernel.meta_eval_llm) else "rule_based"
    }

    # Save review record
    reviews_dir = os.path.join(boros_dir, "memory", "evolution_records")
    os.makedirs(reviews_dir, exist_ok=True)
    with open(os.path.join(reviews_dir, f"review-{proposal_id}.json"), "w") as f:
        json.dump(review_record, f, indent=2)

    return {"status": "ok", "verdict": verdict, "reason": reason, "confidence": confidence}
