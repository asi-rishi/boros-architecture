# Boros — Pre-Build Issue Registry

> 13 issues identified during architecture audit. All resolved in `decisions.md` (decisions 25–35).
> Claude Code must apply these fixes during the build, not after.

---

## Priority Order

Implement fixes in this order. Issues 1 and 2 are prerequisites — nothing else has observable effect without them.

```
ISSUE-001 → ISSUE-002 → ISSUE-003 → ISSUE-004 → ISSUE-005 → ISSUE-006 → ISSUE-007 → ISSUE-008 → ISSUE-009 → ISSUE-010 → ISSUE-011 → ISSUE-012 → ISSUE-013
```

---

## ISSUE-001 — Eval Generator Never Starts

**Severity:** FATAL  
**Decision:** 25  
**Files:** `kernel.py`, `eval-generator/eval_generator.py`

`kernel.py` never spawns `eval_generator.py`. Every EVAL stage times out waiting for a result file that is never written. No scores are ever produced. Compounding never activates.

**Fix:** `kernel.py` spawns the Eval Generator as a subprocess before the boot sequence:

```python
eval_proc = subprocess.Popen(
    ["python", "eval-generator/eval_generator.py"],
    cwd=boros_root
)
```

Kernel polls for `eval-generator/shared/.ready` sentinel with 30-second timeout. Halt if not found. `eval_generator.py` writes `.ready` as its last step before entering its polling loop.

---

## ISSUE-002 — `context_load()` Doesn't Inject Memory Content Into System Prompt

**Severity:** FATAL  
**Decision:** 26  
**Files:** `skills/context-orchestration/functions/context_load.py`, `skills/loop-orchestrator/functions/loop_start.py`

`context_load()` reads memory files and counts tokens but returns only metadata. `loop_start()` has no source for actual memory content. REFLECT is blind — the LLM sees a manifest saying records exist but cannot read them. Every hypothesis is written without any historical context.

**Fix:** `context_load()` returns a `content` key with serialized record text:

```python
return {
    "status": "ok",
    "loaded": loaded,
    "manifest": manifest,
    "content": content    # NEW: actual text for system prompt injection
}
```

`content` format:
```
=== IDENTITY ===
{identity json}

=== SCORE HISTORY ===
{last N score entries}

=== EVOLUTION RECORDS ===
{record 1 json}
...

=== EXPERIENCES ===
{experience 1 json}
...
```

`loop_start()` injects this as block 4 of the system prompt:
```python
context_result = kernel.registry["context_load"]({}, kernel)
memory_content = context_result.get("content", "No memory content loaded.")
system_prompt = "\n\n".join([identity_block, stage_directive, context_manifest_json, memory_content, rules])
```

---

## ISSUE-003 — `evolve_propose()` Doesn't Store Proposed SKILL.md Content

**Severity:** FATAL (bundled with ISSUE-008)  
**Decision:** 27  
**Files:** `skills/meta-evolution/functions/evolve_propose.py`, `skills/meta-evolution/functions/evolve_apply.py`

`evolve_propose()` stores `skillmd_update = None`. `review_proposal()` sends `"[LLM will generate new content]"` as the after-state to GPT-4o. The two highest-weight review dimensions (correctness 0.30, regression risk 0.25) cannot be meaningfully evaluated.

**Fix:** Add `proposed_skillmd` as a required parameter:

```python
evolve_propose(
    target_skill: str,
    change_description: str,
    rationale: str,
    proposed_skillmd: str,    # REQUIRED — full new SKILL.md content
    target_category: str,     # see ISSUE-006
    research_sources: list = []
)
```

Store immediately on the proposal:
```python
proposal["skillmd_update"] = params["proposed_skillmd"]
proposal["diff"]["files_modified"][0]["after"] = params["proposed_skillmd"]
```

---

## ISSUE-004 — Rollback Passes Version String Instead of Snapshot UUID

**Severity:** HIGH (bundled with ISSUE-005)  
**Decision:** 28  
**Files:** `skills/meta-evolution/functions/evolve_rollback.py`

`evolve_rollback()` passes `proposal["old_version"]` (a semantic version string like `"1.2.0"`) as the `snapshot_id` to `forge_rollback()`. No snapshot file named `1.2.0` exists. Every rollback fails silently. The regression guard is broken.

**Fix:** `evolve_rollback()` uses `proposal["snapshot_id"]` (UUID captured in ISSUE-005 fix):

```python
kernel.registry["forge_rollback"](
    {"skill_name": target_skill, "snapshot_id": proposal["snapshot_id"]},
    kernel
)
```

---

## ISSUE-005 — Snapshot UUID Discarded After `forge_snapshot()`

**Severity:** HIGH (bundled with ISSUE-004)  
**Decision:** 28  
**Files:** `skills/meta-evolution/functions/evolve_propose.py`

`forge_snapshot()` returns a UUID-based `snapshot_id`. `evolve_propose()` discards it. The proposal has no record of which snapshot to restore from, making rollback impossible.

**Fix:** Capture and store on proposal:

```python
snap_result = kernel.registry["forge_snapshot"]({"skill_name": target_skill}, kernel)
if snap_result.get("status") != "ok":
    return {"status": "error", "error": f"Snapshot failed: {snap_result.get('error')}"}
snapshot_id = snap_result["snapshot_id"]
proposal["snapshot_id"] = snapshot_id
```

Add `snapshot_id` to proposal schema.

---

## ISSUE-006 — `target_category` Never Set on Proposals

**Severity:** HIGH  
**Decision:** 29  
**Files:** `skills/meta-evolution/functions/evolve_propose.py`, `skills/meta-evolution/SKILL.md`

`evolve_propose()` does not accept or store `target_category`. Every evolution record written to `memory/evolution_records/` has `target_category: "unknown"`. REFLECT cannot build category-to-skill correlations. `evolve_history(category=...)` always returns empty. Compounding is corrupted from cycle 1.

**Fix:** Add `target_category` to `evolve_propose()` signature (see ISSUE-003 fix — it's in the same updated signature). Store on proposal:

```python
proposal["target_category"] = params.get("target_category", "unknown")
```

Add rule to Meta-Evolution SKILL.md: *"Pass the same `target_category` to `evolve_propose()` that you declared in `evolve_set_target()`."*

---

## ISSUE-007 — No Error Policy When `review_proposal()` Fails

**Severity:** MEDIUM  
**Decision:** 30  
**Files:** `skills/meta-evaluation/SKILL.md`

When `review_proposal()` returns `status: error` (OpenAI API failure, rate limit, bad key), there is no SKILL.md instruction for what to do. The LLM may retry indefinitely, stall, or skip review entirely.

**Fix:** Add explicit error policy to Meta-Evaluation SKILL.md:

```
On review_proposal() infrastructure failure:
1. Retry once.
2. If still errors: treat proposal as REJECTED (infrastructure failure).
3. Write experience record: {outcome: "rejected", reason: "meta_eval_infrastructure_failure", ...}
4. Log and call loop_advance_stage("EVAL").
5. Never auto-approve on infrastructure failure.
```

---

## ISSUE-008 — `evolve_apply()` Silently Fails If `updated_skillmd` Omitted

**Severity:** MEDIUM (bundled with ISSUE-003)  
**Decision:** 27  
**Files:** `skills/meta-evolution/functions/evolve_apply.py`

`evolve_apply()` requires `updated_skillmd` from the LLM at call time. If omitted, the function errors and the SKILL.md is never written. The cycle completes with no actual modification, and the Director has no indication.

**Fix:** `updated_skillmd` becomes optional, falling back to `proposal["skillmd_update"]` (which is always populated after ISSUE-003 fix):

```python
updated_skillmd = params.get("updated_skillmd") or proposal.get("skillmd_update")
```

---

## ISSUE-009 — Tests Run Against Pre-Change State, Providing False Assurance

**Severity:** MEDIUM  
**Decision:** 31  
**Files:** `skills/meta-evolution/functions/evolve_propose.py`, `skills/meta-evaluation/functions/_internal/prompt_builder.py`

`forge_test()` is called before the proposed SKILL.md is written. Tests run against the current (unmodified) skill. Results are stored as `test_results` and GPT-4o interprets them as evidence the proposed change is correct. The correctness dimension (weight 0.30) is evaluated against baseline, not the proposal.

**Fix:** Rename the field and correct the framing. Running baseline tests is still useful (failing baseline = skill already broken, hard reject). The deception is in the label:

- Rename field: `test_results` → `baseline_test_results`
- Update `prompt_builder.py`:
  ```python
  f"**Baseline test results (pre-change state):** {proposal.get('baseline_test_results', {})}\n"
  f"Note: Tests verify the skill was functional before this change. They do not test the proposed new behavior.\n"
  ```
- Update correctness dimension description to reflect this.

---

## ISSUE-010 — `score_history.jsonl` Write Responsibility Unspecified

**Severity:** MEDIUM  
**Decision:** 32  
**Files:** `Skill-reference.md` (Eval Bridge spec), `Boros.md §25` (Phase 4 acceptance criteria)

Eval Bridge is a generated skill. If the implementation omits the `score_history.jsonl` write or uses the wrong schema, `evolve_orient()` reads empty scores forever and REFLECT cannot identify weak categories.

**Fix:** Make the write contract explicit in the Eval Bridge spec. `eval_read_scores()` MUST synchronously append to `memory/score_history.jsonl` before returning:

```python
entry = {
    "eval_id": result["eval_id"],
    "timestamp": result["timestamp"],
    "cycle": result["cycle"],
    "scores": result["scores"],
    "composite": result["composite"],
    "deltas": computed_deltas,        # post - pre per category, {} on first eval
    "plateau_flag": False,
    "cycles_since_improvement": {}
}
with open(score_history_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
```

Add to Phase 4 acceptance criteria: *"`evolve_orient()` called immediately after `eval_read_scores()` returns the correct weakest category. Test these two functions together."*

---

## ISSUE-011 — Spot-Check Blocks Loop Indefinitely

**Severity:** LOW  
**Decision:** 33  
**Files:** `config.json`, `skills/loop-orchestrator/functions/loop_end_cycle.py`

Spot-check (every 5 cycles) blocks the loop waiting for Director input. Unattended runs stall at every 5th cycle.

**Fix:** Add `spot_check_timeout_minutes` to `config.json`. Default `0` (blocking — existing behavior unchanged). When non-zero, Loop Orchestrator auto-approves after that duration and writes a memory fact noting the auto-approval.

```json
{ "spot_check_timeout_minutes": 0 }
```

---

## ISSUE-012 — Context Orchestration Not Visible in EVAL Stage

**Severity:** LOW  
**Decision:** 34  
**Files:** `skills/context-orchestration/skill.json`, `manifest.json`

`context-orchestration` has `stage_visibility: ["REFLECT", "EVOLVE"]`. Boros cannot call `context_get_manifest()` during EVAL if needed.

**Fix:** Add `"EVAL"` to `stage_visibility`:

```json
"stage_visibility": ["REFLECT", "EVOLVE", "EVAL"]
```

Update in both `skill.json` and `manifest.json`.

---

## ISSUE-013 — Cycle ID Reads as 0 If `loop_state.json` Missing

**Severity:** LOW  
**Decision:** 35  
**Files:** `skills/meta-evolution/functions/evolve_propose.py`

`evolve_propose()` reads cycle number directly from `loop_state.json`. If the file is missing or corrupt, all proposals are attributed to cycle 0, corrupting cycle-based attribution across all evolution records.

**Fix:** Prefer `loop_get_state()` via kernel registry. Fall back to file read only if unavailable. Add sanity check:

```python
if cycle == 0:
    records_exist = any((root / "memory" / "evolution_records").glob("*.json"))
    if records_exist:
        log("[WARN] evolve_propose: cycle reads as 0 but evolution records exist. loop_state.json may be corrupt.")
```

---

## Summary Table

| Issue | Severity | Component | Fix In |
|-------|----------|-----------|--------|
| ISSUE-001 | **FATAL** | kernel.py, eval_generator.py | Decision 25 |
| ISSUE-002 | **FATAL** | context_load.py, loop_start.py | Decision 26 |
| ISSUE-003 | **FATAL** | evolve_propose.py | Decision 27 |
| ISSUE-004 | High | evolve_rollback.py | Decision 28 |
| ISSUE-005 | High | evolve_propose.py | Decision 28 |
| ISSUE-006 | High | evolve_propose.py, Meta-Evolution SKILL.md | Decision 29 |
| ISSUE-007 | Medium | Meta-Evaluation SKILL.md | Decision 30 |
| ISSUE-008 | Medium | evolve_apply.py | Decision 27 |
| ISSUE-009 | Medium | evolve_propose.py, prompt_builder.py | Decision 31 |
| ISSUE-010 | Medium | Eval Bridge spec, Boros.md §25 | Decision 32 |
| ISSUE-011 | Low | config.json, loop_end_cycle.py | Decision 33 |
| ISSUE-012 | Low | context-orchestration skill.json, manifest.json | Decision 34 |
| ISSUE-013 | Low | evolve_propose.py | Decision 35 |

**Fix 001 and 002 first. Nothing else has observable effect without them.**
