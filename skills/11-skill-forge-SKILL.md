# Skill Forge

You are the safety layer for all skill modifications. Before any SKILL.md gets changed, you snapshot, validate, and test the target skill. After a rejection or regression, you restore from snapshot. You prevent broken changes from landing silently.

---

## Your Role

You are active during **EVOLVE** only. Meta-Evolution calls you as part of the `evolve_propose` flow — you are not called directly by the LLM. You are called by function implementations, not by Boros's reasoning.

You are a tool the system uses, not a tool the LLM calls.

---

## Functions

### forge_snapshot(skill_name)

Saves the current state of a skill before any change is made. Called at the start of every proposal.

Saves to: `skills/{skill_name}/snapshots/snap-{skill_name}-{timestamp}-{uuid4[:8]}.tar.gz`

The snapshot captures: SKILL.md, skill.json, all functions/, all state/ files.

```
→ {"status": "ok", "snapshot_id": "snap-{skill_name}-{timestamp}-{uuid8}"}
→ {"status": "error", "error": str}
```

The `snapshot_id` is stored on the proposal. `evolve_rollback` uses it — not version strings.

### forge_validate(skill_name)

Validates that the skill is structurally sound before proposing a change.

Checks:
1. `SKILL.md` exists and is non-empty
2. `skill.json` is valid JSON with required fields
3. All functions listed in `skill.json` → `provided_functions` are importable from `functions/`

```
→ {"status": "ok", "errors": []}
→ {"status": "ok", "errors": ["SKILL.md missing", "function memory_read not importable"]}
```

A non-empty `errors` list does NOT automatically reject the proposal — that decision is Meta-Evolution's. But it is stored in `baseline_test_results` and triggers a hard fail in Meta-Evaluation (correctness dimension).

### forge_test(skill_name)

Runs the skill's test suite via pytest.

Runs: `pytest skills/{skill_name}/tests/ -v --timeout=30`

```
→ {"status": "ok", "total": int, "passed": int, "failed": int, "failures": [list of failure summaries]}
```

If no tests exist, returns `{"status": "ok", "total": 0, "passed": 0, "failed": 0, "failures": [], "note": "no tests found"}`.

Results are stored as `baseline_test_results` on the proposal. These are **pre-change** results — they verify the skill was functional before the proposal, not that the new behavior is correct.

### forge_apply_diff(skill_name, diff)

Writes the approved content to `SKILL.md`. Called by `evolve_apply`.

`diff` is a dict with `files_modified` list — each entry has `path` and `after` content.

For SKILL.md changes: writes `after` content directly to the file.

```
→ {"status": "ok"}
→ {"status": "error", "error": str}
```

### forge_rollback(skill_name, snapshot_id)

Restores a skill from a snapshot. Called by `evolve_rollback`.

Extracts the snapshot archive and overwrites the skill directory.

```
→ {"status": "ok"}
→ {"status": "error", "error": "snapshot not found" | str}
```

### forge_create_skill(spec)

Creates a full new demand skill directory from a spec.

Spec fields: `name`, `description`, `functions` (list with name/signature/description), `stage_visibility`, `dependencies`.

Creates: skill directory, SKILL.md (generated from spec), skill.json, empty functions/__init__.py, state/, tests/, metrics/metrics.jsonl, snapshots/, changelog.md.

```
→ {"status": "ok", "skill_id": str}
→ {"status": "error", "error": "skill already exists" | str}
```

---

## Rules

1. **Always snapshot before any change.** No proposal proceeds without a snapshot_id.
2. **Snapshot IDs are used for rollback, not version strings.** The snapshot is the canonical save point.
3. **forge_validate errors do not auto-reject.** They are surfaced to Meta-Evaluation as signals.
4. **forge_test results are baseline (pre-change).** They tell Meta-Evaluation if the skill was already broken. They do not test the proposed new behavior.
5. **forge_apply_diff only writes SKILL.md.** It does not modify Python functions — function changes require separate proposals.
6. **forge_rollback is destructive.** It overwrites the skill directory. Call it only when `evolve_rollback` explicitly requests it.

---

## Seed Limitations

- No snapshot pruning — snapshots accumulate indefinitely at seed. Future evolution should add retention policy.
- No diff validation — forge_apply_diff trusts the content it receives.
- forge_test uses a 30-second timeout per skill; no parallelism.
- forge_create_skill generates minimal SKILL.md — quality of generated content improves with evolution.
