
import os, json, uuid, datetime
def evolve_propose(params: dict, kernel=None) -> dict:
    """Create a formal evolution proposal. Stores proposal artifact in session."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    prop_id = f"prop-{uuid.uuid4().hex[:8]}"

    proposal = {
        "id": prop_id,
        "description": params.get("description", ""),
        "target_file": params.get("target_file", ""),
        "diff_summary": params.get("diff_summary", ""),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "status": "pending_review"
    }

    # Read hypothesis context
    hyp_file = os.path.join(boros_dir, "session", "hypothesis.json")
    if os.path.exists(hyp_file):
        with open(hyp_file) as f:
            proposal["hypothesis"] = json.load(f)

    # Save proposal
    proposals_dir = os.path.join(boros_dir, "session", "proposals")
    os.makedirs(proposals_dir, exist_ok=True)
    with open(os.path.join(proposals_dir, f"{prop_id}.json"), "w") as f:
        json.dump(proposal, f, indent=2)

    return {"status": "ok", "proposal_id": prop_id, "proposal": proposal}
