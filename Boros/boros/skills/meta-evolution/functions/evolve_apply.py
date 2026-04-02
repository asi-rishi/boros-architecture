
import os, json, datetime
def evolve_apply(params: dict, kernel=None) -> dict:
    """Commit an approved proposal to the evolution records."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    proposal_id = params.get("proposal_id", "")

    # Read the proposal
    prop_file = os.path.join(boros_dir, "session", "proposals", f"{proposal_id}.json")
    if not os.path.exists(prop_file):
        return {"status": "error", "message": f"Proposal {proposal_id} not found"}

    with open(prop_file) as f:
        proposal = json.load(f)

    proposal["status"] = "applied"
    proposal["applied_at"] = datetime.datetime.utcnow().isoformat() + "Z"

    # Save to evolution records
    records_dir = os.path.join(boros_dir, "memory", "evolution_records")
    os.makedirs(records_dir, exist_ok=True)
    with open(os.path.join(records_dir, f"{proposal_id}.json"), "w") as f:
        json.dump(proposal, f, indent=2)

    # Update proposal status
    with open(prop_file, "w") as f:
        json.dump(proposal, f, indent=2)

    return {"status": "ok", "message": f"Proposal {proposal_id} committed to evolution records."}
