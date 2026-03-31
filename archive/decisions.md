> All decisions consolidated. Apply on top of BOROS.md.

---

## 1. Naming

- Internal codename: **Boros** (was Loki through v12)
- Model name: **ARES** (Autonomous Recursive Evolving System)
- Public product: **Boros**
- Company: **Mumbrane Labs**
- All code, comments, file references, CLI commands use `boros`

---

## 2. Single-Folder Package

Everything lives in one `boros/` folder. No external paths like `~/.loki-snapshots/`. Clone it, set API keys, run it. Everything accumulates inside.

**Changed from:** v12 spec had `~/.loki/`, `~/.loki-snapshots/`, `~/.loki-eval-generator/` as separate locations.

---

## 3. Director Interface (Skill #0)

- Pre-boot, wraps everything else. Not part of health-check sequence.
- Built with `prompt_toolkit`
- Loop runs in background thread; Director types commands in foreground
- Commands split: `status` is immediate, everything else is queued via `commands/pending.json`
- Loop Orchestrator reads and clears pending commands at cycle boundaries

---

## 4. World Model

- Director edits `world_model.json` directly (flat file, no editor UI)
- Lives inside `boros/` folder
- Boros reads at cycle start via derived `evals/categories.json` (names + descriptions + scores only)
- Boros does NOT see rubrics, weights, or test questions
- Changing a category definition resets its high-water mark

---

## 5. Memory Architecture

- Memory functions read/write to `boros/memory/` (top-level), NOT `boros/skills/memory/state/`
- `skills/memory/state/` stays empty — placeholder
- Seed strategy: full corpus dump, 8k token cap, oldest dropped first
- `memory_read(query)` accepts query but ignores it at seed — interface stable for future evolution
- Evolution records never decay

---

## 6. Session vs Memory Lifecycle

| Location               | Lifecycle                            | Purpose                                  |
| ---------------------- | ------------------------------------ | ---------------------------------------- |
| `session/`             | One cycle — cleared at start of next | Hypothesis, context manifest, scratchpad |
| `memory/`              | Forever                              | Evolution records, experiences, scores   |
| `skills/*/snapshots/`  | Until pruned                         | Per-proposal skill rollback points       |
| `snapshots/eval-{id}/` | Last 10 + every 10th forever         | System-level rollback                    |

---

## 7. REFLECT → EVOLVE Handoff

- Hypothesis is a **written artifact** — LLM must call `reflection_write_hypothesis()` before transition
- Loop Orchestrator hard-gates EVOLVE on artifact existence
- EVOLVE loads hypothesis from session state, not conversation history
- If hypothesis missing after REFLECT, one retry. Still missing = failed cycle.

---

## 8. Evolution Loop Design

- REFLECT → EVOLVE → EVAL (3 stages, 3+ LLM calls per cycle)
- Conversation history carries forward **within** a cycle
- At cycle end, history is **discarded** — fresh conversation next cycle
- EVAL every cycle (changed from "every 10 cycles" in earlier versions)
- Single-proposal discipline for first 20 cycles
- Modification band: 5-50 lines per change

---

## 9. Meta-Evaluation

- Uses GPT-4o (different model family) via `kernel.meta_eval_llm`
- Reviews diff only, not full skill file
- Synchronous and blocking during EVOLVE
- Permissive early (threshold 0.55 at cycles 1-10), strict later (0.70 at cycles 31+)
- Max 3 modification rounds, then auto-reject

---

## 10. Eval Generator

- Separate process, separate LLM connection, inside `boros/eval-generator/`
- File-based communication only (request files → result files)
- Boros cannot see, access, or influence it
- Difficulty scaling: composite <0.60 → L1, 0.60-0.74 → L2, 0.75-0.84 → L3, 0.85+ → L4
- Bumps after 3 consecutive evals above threshold
- Tests are no-tools, raw output only

---

## 11. Director Commands

- `boros inject "..."` is the primary soft-steering mechanism — writes to Memory, REFLECT loads at high priority
- All commands execute between cycles (except `status` which is immediate)
- Commands write to `commands/pending.json`; Loop Orchestrator consumes at cycle boundary
- Spot-check every 5 cycles: `boros approve` or `boros flag "reason"`

---

## 12. Open Source Strategy

**Open source (cloneable):** Kernel, all 19 skills with seed SKILL.md files, eval harness, Director Interface, world model schema. Empty memory, empty evolution records. Anyone can clone, define categories, plug in API keys, start evolving.

**Closed source (Mumbrane Labs IP):** Prime Boros's evolution records (accumulated intelligence), all domain forks. The moat is the records, not the code.

---

## 13. Seed Skills Priority

4 critical seed skills must be hand-written with high quality. Errors in these propagate from cycle one:

1. **Memory** — everything reads from it
2. **Context Orchestration** — defines what the LLM sees
3. **Meta-Evolution** — defines how changes are proposed
4. **Meta-Evaluation** — defines how changes are reviewed

---

## 14. Environment

- `.env` file with `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`
- Kernel reads via `dotenv`
- Primary substrate: `claude-sonnet-4-20250514` (configurable in manifest)
- No database, no framework, no orchestration layer — intentionally minimal

---

## 15. Kernel Message Loop

The kernel owns the mechanical send/receive/dispatch loop — dumb plumbing, no intelligence. It sends messages to Claude, receives responses, dispatches tool_use blocks to the registry, and sends results back. The LLM controls stage transitions by calling Loop Orchestrator tools (`loop_advance_stage`, `loop_end_cycle`). When `loop_end_cycle` is called, the kernel discards conversation history and starts fresh. This keeps the kernel at ~50 lines while all intelligence stays in skills.

---

## 16. Python Imports for Hyphenated Directories

Skill directories use hyphens (`meta-evolution/`) per the spec. Python can't import hyphenated names directly. The kernel's skill loader uses `importlib` with path-based loading to resolve this. Directory names stay hyphenated.

---

## 17. Eval Generator — No Kernel Boot

"Read-only Boros copy" means: read all SKILL.md files + `identity.json` from the filesystem, assemble into a system prompt, send test prompts as standalone Claude API calls. No second kernel boot, no tools, no process spawn. "Read-only" = reads files, doesn't write anything.

---

## 18. Snapshot Manager — Eval Bridge Owns It

No separate Snapshot Manager skill. System-level snapshots (post-eval) are handled by Eval Bridge as an internal helper after `eval_update_high_water`. Per-proposal snapshots remain Skill Forge's job. System rollback (`boros rollback N`) is handled by Director Interface directly — infrastructure, not LLM-facing.

---

## 19. Git Tagging — Eval Bridge

After system snapshot, Eval Bridge shells out `git tag eval-{id}-score-{composite}`. If git isn't initialized, skip silently.

---

## 20. System Prompt Construction

Loop Orchestrator's `loop_start()` assembles the system prompt from:
1. Identity block (from `identity.json`)
2. Stage directive (e.g., "You are in REFLECT stage. Analyze scores and write a hypothesis.")
3. Context manifest (from Context Orchestration — what's loaded, what's not)
4. Loaded memory content (the actual records Context Orchestration selected)
5. Rules ("Call `loop_advance_stage` when done with this stage.")

Stage directives are short strings in Loop Orchestrator. Evolvable — Boros can rewrite them via Meta-Evolution.

---

## 21. world_model.json Ships Pre-filled

Rubrics are fully defined in the spec. Ship them pre-filled. The Eval Generator needs rubrics to score. Empty rubrics = EVAL fails on cycle 1. Director can edit later.

---

## 22. Staged Model Strategy

Claude Pro (claude.ai) does not include API access — you need a separate account at `console.anthropic.com`. To minimize API costs in early cycles, use a cheaper substrate:

| Phase | Cycles | Recommended model | Approx cost/cycle |
|-------|--------|-------------------|-------------------|
| Bootstrap | 1–30 | `claude-haiku-4-5-20251001` | ~$0.05–0.15 |
| Signal | 30–60 | `claude-sonnet-4-6` | ~$2–5 |
| Acceleration | 60–100 | `claude-sonnet-4-6` | ~$2–5 |
| Plateau | 100+ | `claude-opus-4-6` | ~$10–20 |

Change the model by editing `boros/manifest.json` → `llm.primary.model`. No restart required — takes effect next cycle.

Haiku is sufficient for bootstrap because the system is hypothesis-driven with no score data yet. The quality of the substrate matters more once evolution records start compounding (cycle 30+).

---

## 23. Phase 4 Scope — 15 Skills

Context Orchestration's Python functions come from seed skills. Phase 4 generates its SKILL.md plus implements the other 15 skills' functions and SKILL.md files. Total: 15 skills needing function implementations, plus Context Orchestration needing only its SKILL.md.

---

## 24. What Changed Across Versions

| Version | Key Change                                                                                                              |
| ------- | ----------------------------------------------------------------------------------------------------------------------- |
| v1-v6   | Architecture iterations (layers, skills, hooks)                                                                         |
| v7      | Eval Generator replaces manual test design                                                                              |
| v8      | Dual mode (evolution + work), 12 categories formalized                                                                  |
| v9      | REFLECT → EVOLVE → EVAL (3-stage loop)                                                                                  |
| v10     | World Model replaces "blind eval" terminology                                                                           |
| v11     | Runtime model clarified, per-stage API calls                                                                            |
| v12     | Full spec written for Claude Code                                                                                       |
| BOROS   | Renamed from Loki. Single-folder. Director Interface added. 19 skills (was 18). Context Orchestration seed skill added. |

---

---

# Gap Fixes — Architecture Audit Decisions

> These decisions resolve 13 open issues identified during pre-build audit. Each decision references the issue ID, names the affected files, and specifies the exact change. Apply on top of BOROS.md and Seed-skills.md.

---

## 25. Eval Generator Startup (ISSUE-001)

**Problem:** `python kernel.py` never starts `eval_generator.py`. Every EVAL stage times out. No scores ever written. Compounding never activates.

**Decision:** `kernel.py` starts the Eval Generator as a subprocess immediately before the boot sequence, before any skill is loaded.

```python
import subprocess
eval_proc = subprocess.Popen(
    ["python", "eval-generator/eval_generator.py"],
    cwd=boros_root
)
```

After spawning, kernel polls for `eval-generator/shared/.ready` sentinel file (written by the Eval Generator on successful startup) with a 30-second timeout. If the sentinel does not appear, kernel halts with:

```
[BOROS HALT] Eval Generator failed to start. Check OPENAI_API_KEY and eval-generator/config.json.
```

`eval_generator.py` writes `.ready` as its last step before entering its polling loop.

**Files changed:** `kernel.py`, `eval-generator/eval_generator.py`

**Note:** The Eval Generator process is a child of the kernel process. If the kernel is killed (Ctrl+C at cycle boundary), the child is also terminated. No orphan processes.

---

## 26. Context Load Must Return Actual Memory Content (ISSUE-002)

**Problem:** `context_load()` reads memory files and counts tokens but returns only metadata. `loop_start()` specifies "loaded memory content" as block 4 of the system prompt, but has no source for it. REFLECT is blind — it sees a manifest saying records are loaded but cannot read them.

**Decision:** `context_load()` return schema gains a `content` key containing the serialized text of all selected records. `loop_start()` uses this as block 4 of the system prompt directly.

**`context_load()` return schema — updated:**

```python
return {
    "status": "ok",
    "loaded": loaded,      # token counts per category (unchanged)
    "manifest": manifest,  # metadata summary (unchanged)
    "content": content     # NEW: actual text for system prompt injection
}
```

`content` is a single string, formatted as structured sections:

```
=== IDENTITY ===
{identity json}

=== SCORE HISTORY ===
{last N score entries}

=== EVOLUTION RECORDS ===
{record 1 json}
{record 2 json}
...

=== EXPERIENCES ===
{experience 1 json}
...
```

The existing token-counting loop already reads each file. Store the text alongside the count rather than discarding it. No second filesystem read required.

`loop_start()` system prompt assembly — block 4 updated:

```python
context_result = kernel.registry["context_load"]({}, kernel)
memory_content = context_result.get("content", "No memory content loaded.")

system_prompt = "\n\n".join([
    identity_block,
    stage_directive,
    context_manifest_json,
    memory_content,        # block 4: actual records
    rules
])
```

**Files changed:** `skills/context-orchestration/functions/context_load.py`, `skills/loop-orchestrator/functions/loop_start.py`

---

## 27. evolve_propose() Must Accept and Store Proposed SKILL.md Content (ISSUE-003 + ISSUE-008)

**Problem (ISSUE-003):** `evolve_propose()` saves `skillmd_update = None`. `review_proposal()` sends `"[LLM will generate new content]"` as the after-state to GPT-4o. The two highest-weight review dimensions (correctness 0.30, regression 0.25) cannot be evaluated.

**Problem (ISSUE-008):** `evolve_apply()` requires `updated_skillmd` from the LLM at call time. If omitted, apply silently fails. The LLM must know to re-pass the full content it already wrote.

**Decision:** Add `proposed_skillmd` as a required parameter to `evolve_propose()`. The LLM writes the complete new SKILL.md content before calling `evolve_propose()` and passes it in. This is the natural order — you must know what you want to change before proposing it.

**`evolve_propose()` signature — updated:**

```python
evolve_propose(
    target_skill: str,
    change_description: str,
    rationale: str,
    proposed_skillmd: str,    # NEW — full new SKILL.md content, required
    research_sources: list = []
)
```

`evolve_propose()` stores it immediately:

```python
proposal["skillmd_update"] = params["proposed_skillmd"]
proposal["diff"]["files_modified"][0]["after"] = params["proposed_skillmd"]
```

By the time `review_proposal()` fires, `after` is populated. GPT-4o receives real content for all five dimensions.

**`evolve_apply()` — updated:** `updated_skillmd` becomes optional, falling back to `proposal["skillmd_update"]`:

```python
updated_skillmd = params.get("updated_skillmd") or proposal.get("skillmd_update")
```

Since `proposed_skillmd` is now always stored on the proposal, `evolve_apply(proposal_id=...)` without the content param works correctly. The LLM does not need to re-pass it.

**Boros.md function signatures — updated:**
- `evolve_propose(target_skill, change_description, rationale, proposed_skillmd, research_sources=[])` 
- `evolve_apply(proposal_id, updated_skillmd="")` — updated_skillmd now optional

**Files changed:** `skills/meta-evolution/functions/evolve_propose.py`, `skills/meta-evolution/functions/evolve_apply.py`, `Boros.md §12`

---

## 28. Snapshot ID Tracked on Proposal — Rollback Uses It (ISSUE-004 + ISSUE-005)

**Problem (ISSUE-005):** `forge_snapshot()` returns a UUID-based `snapshot_id`. `evolve_propose()` discards it. The proposal has no record of which snapshot to restore from.

**Problem (ISSUE-004):** `evolve_rollback()` passes `proposal["old_version"]` (a semantic version string like `"1.2.0"`) as the `snapshot_id` to `forge_rollback()`. No file named `1.2.0` exists in snapshots. Every rollback fails silently. The regression guard is broken.

**Decision:** Capture the snapshot_id from `forge_snapshot()` and store it on the proposal. `evolve_rollback()` uses it.

**`evolve_propose()` — updated snapshot call:**

```python
snap_result = kernel.registry["forge_snapshot"]({"skill_name": target_skill}, kernel)
if snap_result.get("status") != "ok":
    return {"status": "error", "error": f"Snapshot failed: {snap_result.get('error')}"}
snapshot_id = snap_result["snapshot_id"]   # capture

proposal["snapshot_id"] = snapshot_id      # store on proposal
```

**`evolve_rollback()` — updated forge call:**

```python
kernel.registry["forge_rollback"](
    {"skill_name": target_skill, "snapshot_id": proposal["snapshot_id"]},
    kernel
)
```

**Proposal schema — `snapshot_id` field added:**

```json
{
  "proposal_id": "prop-...",
  "snapshot_id": "snap-{uuid}",
  ...
}
```

**Files changed:** `skills/meta-evolution/functions/evolve_propose.py`, `skills/meta-evolution/functions/evolve_rollback.py`, `Boros.md §12` (proposal schema)

---

## 29. target_category Passed Through evolve_propose() and Stored on Proposal (ISSUE-006)

**Problem:** `evolve_propose()` does not accept or store `target_category`. Every evolution record written to `memory/evolution_records/` has `target_category: "unknown"`. REFLECT cannot build category-to-skill correlations. `evolve_history(category=...)` always returns empty. Compounding degrades.

**Decision:** Add `target_category` as a parameter to `evolve_propose()`. The LLM already called `evolve_set_target(category=...)` immediately before — the value is in context.

**`evolve_propose()` signature — updated:**

```python
evolve_propose(
    target_skill: str,
    change_description: str,
    rationale: str,
    proposed_skillmd: str,
    target_category: str,     # NEW — must match category passed to evolve_set_target()
    research_sources: list = []
)
```

Store it on the proposal:

```python
proposal["target_category"] = params.get("target_category", "unknown")
```

`evolve_apply()` already reads `proposal.get("target_category", "unknown")` when writing the evolution record — no change needed there.

**SKILL.md for Meta-Evolution — updated rule:** "Pass the same `target_category` to `evolve_propose()` that you declared in `evolve_set_target()`."

**Files changed:** `skills/meta-evolution/functions/evolve_propose.py`, `skills/meta-evolution/SKILL.md`

---

## 30. Meta-Evaluation Error Policy (ISSUE-007)

**Problem:** When `review_proposal()` returns `status: error` (OpenAI API failure, invalid key, rate limit), Boros has no SKILL.md instruction for what to do. The LLM may retry indefinitely, stall, or skip review — all against the rules or against the evolution objective.

**Decision:** Add an explicit error policy to Meta-Evaluation's SKILL.md. No code change required.

**Meta-Evaluation SKILL.md — new rule added under "Rules":**

```
### On review_proposal() infrastructure failure

If review_proposal() returns {"status": "error"}, do not stall. Follow this sequence:

1. Retry once after waiting (call review_proposal() again with the same proposal_id).
2. If it errors again, treat the proposal as REJECTED due to infrastructure failure.
3. Write an experience record via memory_write():
   type: "experience"
   content: {
     "outcome": "rejected",
     "reason": "meta_eval_infrastructure_failure",
     "error": <error message from tool result>,
     "tags": ["infrastructure_failure", "meta_eval"]
   }
4. Log: "Meta-evaluation unavailable. Proposal <id> rejected. Advancing to EVAL."
5. Call loop_advance_stage("EVAL"). Do not attempt further proposals this cycle.

Never auto-approve on infrastructure failure. Rejection is the safe default.
```

**Files changed:** `skills/meta-evaluation/SKILL.md`

---

## 31. Baseline Test Step Renamed for Honesty (ISSUE-009)

**Problem:** `forge_test()` runs tests against the pre-change skill state, not the proposed change. The proposal stores this as `test_results` and GPT-4o interprets it as evidence the proposed change produces correct behavior. This is false assurance — the highest-weight dimension (correctness, 0.30) is evaluated against baseline, not the proposal.

**Decision:** Rename the field and update the meta-evaluation prompt to accurately describe what is being tested. No change to test execution — running baseline tests before a change is genuinely useful (a failing baseline = the skill is already broken, hard reject). The framing is corrected, not the behavior.

**Proposal schema — field renamed:**

```json
{
  "baseline_test_results": { "total": 3, "passed": 3, "failed": 0, "failures": [] }
}
```

**`_internal/prompt_builder.py` — test results section updated:**

```python
f"**Baseline test results (pre-change state):** {proposal.get('baseline_test_results', {})}\n"
f"Note: Tests verify the skill was functional before this change. They do not test the proposed new behavior.\n"
```

**`_internal/prompt_builder.py` — correctness dimension description updated:**

```
correctness (weight 0.30): Does the change description logically produce correct behavior?
Hard fail: baseline tests were already failing before this change.
Evaluate: rationale quality, logical soundness of the described change, consistency with SKILL.md before/after.
```

**Files changed:** `skills/meta-evolution/functions/evolve_propose.py` (rename field), `skills/meta-evaluation/functions/_internal/prompt_builder.py` (update prompt)

---

## 32. Eval Bridge score_history.jsonl Write — Explicit Contract (ISSUE-010)

**Problem:** `score_history.jsonl` writes are assigned to Eval Bridge but the implementation is generated (Phase 4), not seeded. If the implementation omits the write or uses a wrong schema, `evolve_orient()` reads empty scores forever.

**Decision:** Make the write contract explicit in the Eval Bridge spec and add a two-sided acceptance test.

**Eval Bridge `eval_read_scores()` — specification updated:**

After reading the result file and before returning, `eval_read_scores()` MUST append to `memory/score_history.jsonl`:

```python
entry = {
    "eval_id": result["eval_id"],
    "timestamp": result["timestamp"],
    "cycle": result["cycle"],
    "scores": result["scores"],
    "composite": result["composite"],
    "deltas": computed_deltas,          # post - pre per category, {} on first eval
    "plateau_flag": False,              # set True if composite unchanged for 3+ evals
    "cycles_since_improvement": {}      # per-category counter
}
with open(score_history_path, "a") as f:
    f.write(json.dumps(entry) + "\n")
```

This must happen synchronously before `eval_read_scores()` returns. Callers depend on it.

**Phase 4 acceptance criteria — updated (Boros.md §25):**

Add to Eval Bridge acceptance criteria: "`eval_read_scores()` appends a correctly-shaped entry to `memory/score_history.jsonl`. `evolve_orient()` called immediately after returns the correct weakest category from the written scores. Test these two functions together."

**Files changed:** `Skill-reference.md` (Eval Bridge spec), `Boros.md §25` (Phase 4 acceptance criteria)

---

## 33. Spot-Check Auto-Approve Timeout (ISSUE-011)

**Problem:** Spot-check blocks the loop indefinitely waiting for Director input. Unattended runs halt at every 5th cycle.

**Decision:** Add `spot_check_timeout_minutes` to `config.json`. Default `0` (blocking — existing behavior unchanged). When set to a non-zero value, Loop Orchestrator auto-approves after that duration and logs the event.

**`config.json` — new field:**

```json
{
  "director_spot_check_frequency": 5,
  "spot_check_timeout_minutes": 0,
  ...
}
```

**Loop Orchestrator spot-check behavior — updated:**

```python
if spot_check_timeout > 0:
    # Wait up to timeout, then auto-approve
    if elapsed_minutes >= spot_check_timeout:
        log("[SPOT-CHECK] No Director input after {timeout}min. Auto-approved. Continuing.")
        proceed = True
else:
    # Block until explicit approve/flag (existing behavior)
    proceed = wait_for_director_command()
```

Auto-approval writes a fact to memory: `{"type": "fact", "content": "Spot-check at cycle N auto-approved after timeout — no Director input."}` so REFLECT is aware.

**Files changed:** `config.json`, `skills/loop-orchestrator/functions/loop_end_cycle.py`

---

## 34. Context Orchestration Visible in EVAL Stage (ISSUE-012)

**Problem:** `context-orchestration` has `stage_visibility: ["REFLECT", "EVOLVE"]`. The spec says it fires at cycle start, but Boros cannot call `context_get_manifest()` during EVAL if needed.

**Decision:** Add `"EVAL"` to `stage_visibility` in both `skill.json` and `manifest.json`.

**`skills/context-orchestration/skill.json` — updated:**

```json
"stage_visibility": ["REFLECT", "EVOLVE", "EVAL"]
```

**`manifest.json` — updated:**

```json
"context-orchestration": {
    "stage_visibility": ["REFLECT", "EVOLVE", "EVAL"],
    ...
}
```

**Files changed:** `skills/context-orchestration/skill.json`, `manifest.json`

---

## 35. Cycle ID Fallback When loop_state.json Is Missing (ISSUE-013)

**Problem:** `evolve_propose()` reads the cycle number from `loop_state.json`. If the file is missing or returns 0 incorrectly, all proposals and evolution records are attributed to cycle 0, corrupting cycle-based attribution in all records.

**Decision:** `evolve_propose()` uses `loop_get_state()` via the kernel registry as the authoritative source, falling back to file read only if the function is unavailable. Add a sanity check: if cycle reads as 0 but evolution records already exist, log a warning.

**`evolve_propose()` — cycle read updated:**

```python
# Prefer loop_get_state() over direct file read
cycle = 0
if kernel and "loop_get_state" in kernel.registry:
    try:
        state = kernel.registry["loop_get_state"]({}, kernel)
        cycle = state.get("cycle", 0)
    except Exception:
        pass

if cycle == 0:
    # Fallback: direct file read
    loop_path = root / "skills" / "loop-orchestrator" / "state" / "loop_state.json"
    if loop_path.exists():
        try:
            cycle = json.loads(loop_path.read_text()).get("cycle", 0)
        except (json.JSONDecodeError, OSError):
            pass

# Sanity check
if cycle == 0:
    records_exist = any((root / "memory" / "evolution_records").glob("*.json"))
    if records_exist:
        log("[WARN] evolve_propose: cycle reads as 0 but evolution records exist. "
            "loop_state.json may be corrupt. Proceeding with cycle=0.")
```

**Files changed:** `skills/meta-evolution/functions/evolve_propose.py`

---

## Gap Fix Summary

| Decision | Issue(s) | Severity | Files Changed |
|---|---|---|---|
| 25 | ISSUE-001 | Fatal | `kernel.py`, `eval-generator/eval_generator.py` |
| 26 | ISSUE-002 | Fatal | `context_load.py`, `loop_start.py` |
| 27 | ISSUE-003 + ISSUE-008 | High + Medium | `evolve_propose.py`, `evolve_apply.py` |
| 28 | ISSUE-004 + ISSUE-005 | High + High | `evolve_propose.py`, `evolve_rollback.py` |
| 29 | ISSUE-006 | High | `evolve_propose.py`, Meta-Evolution `SKILL.md` |
| 30 | ISSUE-007 | Medium | Meta-Evaluation `SKILL.md` |
| 31 | ISSUE-009 | Medium | `evolve_propose.py`, `prompt_builder.py` |
| 32 | ISSUE-010 | Medium | `Skill-reference.md`, `Boros.md §25` |
| 33 | ISSUE-011 | Low | `config.json`, `loop_end_cycle.py` |
| 34 | ISSUE-012 | Low | `skill.json` (context-orchestration), `manifest.json` |
| 35 | ISSUE-013 | Low | `evolve_propose.py` |

**Decisions 25 and 26 are prerequisite to all others.** Without the Eval Generator running and without memory content in context, no other fix has observable effect. Implement in order: 25 → 26 → 27 → 28 → 29 → 30–35.

---

## Architecture Improvement Batch (Decisions 36–46)

Applied 2026-03-31. Eleven fixes addressing eval calibration, signal independence, evolution guidance, failure learning, exploration, early-cycle direction, adaptive regression, context staging, visibility, and retrieval quality.

---

## 36. Ground Truth Calibration Anchors (Critical)

**Problem:** Eval Generator and Meta-Evaluation had no concrete behavioral reference for what level_2 vs level_4 looks like per category. Rubric text is descriptive; evaluators need examples to calibrate reliably.

**Decision:** Add `level_2_example` and `level_4_example` fields to each category in `world_model.json`. These are short (50–150 word) representative response fragments showing what level_2 and level_4 quality actually look like in practice.

Meta-Evaluation's `prompt_builder.py` includes these examples in every GPT-4o review prompt for the target category. The Correctness dimension is now scored against observable behavioral targets rather than abstract descriptions.

**Files changed:** `world_model.json`, `skills/09-meta-evaluation-SKILL.md`

---

## 37. Category Independence Enforcement (Critical)

**Problem:** Some scoring categories (notably self_model_fidelity/epistemic_calibration and complexity_navigation/coherence_under_load) measure related but distinct behaviors. Without independence guidance, evaluators may double-count signal across categories, inflating correlations and misleading REFLECT.

**Decision:** Add `independence_from` field to each category in `world_model.json`. The field is an object mapping potentially correlated category names to a concise note explaining how to evaluate them on separate axes. Categories with no high-correlation neighbors have an empty or absent `independence_from`.

Key separations enforced:
- SMF: per-claim annotation accuracy | EC: uncertainty propagation through chains
- CN: input comprehension fidelity | CUL: output constraint satisfaction
- RA: strategy selection across all problems | HE: generate-eliminate-commit cycle for competing explanations

**Files changed:** `world_model.json`

---

## 38. Skill→Category Targeting Map (Critical)

**Problem:** REFLECT had no structured guidance on which skill to change to affect which category. This led to random targeting early on, slow hypothesis compounding, and wasted cycles on infrastructure skills with no cognitive impact.

**Decision:** Create `skill-category-map.json` mapping each of the 19 skills to `primary` and `secondary` categories plus a rationale. Also defines `high_leverage_skills` (reasoning, reflection, research, attention) and `infrastructure_skills` (never target for cognitive evolution).

Reflection reads this file to select the best skill for the target category. Meta-Evolution checks this file before finalizing a proposal — if the target skill is not a primary lever for the target category, it flags the mismatch.

**Files changed:** `skill-category-map.json` (new), `skills/07-reflection-SKILL.md`, `skills/08-meta-evolution-SKILL.md`

---

## 39. Failure Pattern Extraction (Critical)

**Problem:** When the same type of change was proposed and rejected multiple times, REFLECT had no mechanism to detect the pattern and avoid repeating it. This caused proposal thrashing — cycles wasted on known-failing change types.

**Decision:** Add `reflection_extract_failure_patterns()` function to Reflection. Called automatically after cycle 10 within `reflection_analyze()`. Scans evolution records in context for rejected/regressed proposals to the same skill with the same change_type. Writes extracted patterns to `state/failure_patterns.jsonl`.

`reflection_write_hypothesis` gains a `failure_patterns_avoided` field — a list of pattern IDs the current hypothesis explicitly is not repeating. This field propagates into the hypothesis and evolution record.

Thrashing detection: if the same skill has been targeted 3+ times with no improvement, `thrashing_detected: true` is returned and Reflection should move to a different primary skill.

**Files changed:** `skills/07-reflection-SKILL.md`

---

## 40. Fixed Seed Prompts per Category (Critical)

**Problem:** Eval Generator tests were entirely generated per-cycle with no fixed reference points. This introduced noise — a test that happens to be easy produces inflated scores; a hard test produces deflated ones. No cross-cycle comparability.

**Decision:** Add `seed_prompts` field to each category in `world_model.json` with `edge` (boundary-testing) and `adversarial` (manipulation-resistant) prompts. The Eval Generator always includes these fixed prompts in its test battery, supplementing its generated tests.

Fixed prompts ensure every eval cycle includes at least two calibrated reference points per category, enabling cross-cycle score comparability.

**Files changed:** `world_model.json`

---

## 41. Exploration Cycles to Prevent Local Maxima (Important)

**Problem:** Directed evolution always targets the weakest category. This creates local maxima risk: the system may stop improving a category once it reaches a local optimum, missing higher-impact changes that could unlock further gains if explored.

**Decision:** Every `exploration_interval` cycles (default: 10, from `config.json`), Meta-Evolution runs an exploration cycle. Instead of targeting the weakest category, it randomly selects a category from the top 5 scorers and proposes a change to a randomly chosen primary skill for that category.

Exploration proposals are tagged `exploration: true` on the record. Normal Meta-Evaluation review applies — exploration cycles do not bypass quality gates.

**Files changed:** `skills/08-meta-evolution-SKILL.md`

---

## 42. Bootstrap Guidance for Early Cycles (Important)

**Problem:** Cycles 1–9 have no score data. REFLECT was instructed to use "structural reasoning" but given no concrete starting points, leading to highly variable first-cycle hypotheses with low expected quality.

**Decision:** Create `bootstrap-guidance.json` with 9 pre-seeded structural hypotheses, one per bootstrap cycle, targeting 9 different categories. Each entry includes a `structural_check` field — a condition to verify in the actual SKILL.md before adopting the hypothesis.

Reflection reads this file in bootstrap phase and uses the matching entry as a starting point, adapting based on observed SKILL.md content. This seeds the first 9 cycles with structurally sound hypotheses grounded in known architecture gaps rather than uninformed guesses.

**Files changed:** `bootstrap-guidance.json` (new), `skills/07-reflection-SKILL.md`

---

## 43. Adaptive Regression Threshold (Important)

**Problem:** The static 0.02 regression threshold was too strict for early cycles (high score variance expected; experimentation should be tolerated) and sufficient but untuned for later cycles.

**Decision:** Replace the static threshold with a cycle-based step function in `eval_check_regression()`:

| Cycles | Threshold |
|--------|-----------|
| 1–10   | 0.05      |
| 11–30  | 0.03      |
| 31+    | 0.02      |

The `threshold_used` value is logged in the regression check result for later analysis. Future evolution can replace the step function with a smooth decay curve fitted to observed score variance.

**Files changed:** `skills/18-eval-bridge-SKILL.md`

---

## 44. Stage-Specific Context Profiles (Important)

**Problem:** Context Orchestration used two profiles (evolution vs. work) but had no per-stage differentiation within evolution mode. REFLECT, EVOLVE, and EVAL have different context needs: REFLECT needs dense history; EVOLVE needs the current proposal context; EVAL needs minimal loading.

**Decision:** Add three evolution-mode profiles: REFLECT (default, maximizes evolution records at 52%), EVOLVE (reduces records to 30%, expands task context for proposal-related material at 30%), and EVAL (maximizes scores at 30% with moderate experiences).

The REFLECT profile is the automatic default for evolution-mode cycle start. EVOLVE and EVAL profiles are selectable via the `focus` parameter on `context_load()`. Loop Orchestrator can optionally pass `focus` at stage transitions in future evolution.

**Files changed:** `skills/06-context-orchestration-SKILL.md`

---

## 45. `boros explain` Command (Nice-to-have)

**Problem:** The Director could see scores in the TUI but had no quick way to understand *why* the system was making the choices it was — which category is targeted, what hypothesis is active, what failure patterns have been detected, when exploration is next due.

**Decision:** Add `boros explain` command to Director Interface. Executes immediately (does not queue). Prints: weakest category, current target + hypothesis, 5-eval score trends, detected failure patterns, remaining categories queue, and cycles until next exploration. Reads from `session/hypothesis.json`, `memory/score_history.jsonl`, `state/failure_patterns.jsonl`, and `loop_state.json`.

**Files changed:** `skills/00-director-interface-SKILL.md`

---

## 46. Priority-Weighted Memory Retrieval (Nice-to-have)

**Problem:** `memory_read()` returned records in arbitrary chronological order. Under token caps, this meant recent high-value evolution records could be dropped in favor of older low-value session records.

**Decision:** Add priority scoring to `memory_read()`. Score = `type_weight × recency_weight`. Type weights: evolution_record 1.0, experience 0.9, fact 0.7, session 0.5, task_record 0.4. Recency weight: `1 / (1 + days_old)`. A `priority` param allows callers to boost specific types (evolution mode boosts evolution_records ×1.5; work mode boosts task_records ×2.0).

Drop order under token cap: lowest-score records dropped first within the sessions and facts stores. Evolution records and experiences are never dropped. Scores are computed at read time — never stored on records.

**Files changed:** `skills/04-memory-SKILL.md`

---

## Architecture Improvement Summary

| Decision | Fix | Impact | Files Changed |
|---|---|---|---|
| 36 | Ground truth calibration anchors | Critical | `world_model.json`, `09-meta-evaluation-SKILL.md` |
| 37 | Category independence enforcement | Critical | `world_model.json` |
| 38 | Skill→category targeting map | Critical | `skill-category-map.json` (new), `07-reflection-SKILL.md`, `08-meta-evolution-SKILL.md` |
| 39 | Failure pattern extraction | Critical | `07-reflection-SKILL.md` |
| 40 | Fixed seed prompts per category | Critical | `world_model.json` |
| 41 | Exploration cycles | Important | `08-meta-evolution-SKILL.md` |
| 42 | Bootstrap guidance | Important | `bootstrap-guidance.json` (new), `07-reflection-SKILL.md` |
| 43 | Adaptive regression threshold | Important | `18-eval-bridge-SKILL.md` |
| 44 | Stage-specific context profiles | Important | `06-context-orchestration-SKILL.md` |
| 45 | `boros explain` command | Nice-to-have | `00-director-interface-SKILL.md` |
| 46 | Priority-weighted memory retrieval | Nice-to-have | `04-memory-SKILL.md` |
