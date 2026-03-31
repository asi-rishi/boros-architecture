# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Boros** is a self-evolving AI system by **Mumbrane Labs**. Internal codename: **Boros**. System model name: **ARES** (Autonomous Recursive Evolving System). Public product name: **Axiom**.

The system starts minimal and improves itself by rewriting its own skill files, testing changes, scoring results, and rolling back regressions — all autonomously.

**Current status (2026-03-31):** Architecture complete and verified. All 13 pre-build issues resolved in both `Boros.md` (spec) and `Seed-skills.md` (implementation). Seed skill SKILL.md files (`04-memory-SKILL.md`, `06-context-orchestration-SKILL.md`, `08-meta-evolution-SKILL.md`, `09-meta-evaluation-SKILL.md`) verified accurate. Ready for Phase 1 build. Implementation follows the 8-phase build order in `build-order.md`.

## Model Configuration & Cost

Configure primary substrate in `boros/manifest.json` → `llm.primary.model`. Takes effect next cycle (no restart required).

| Phase | Cycles | Model | Approx cost/cycle |
|-------|--------|-------|-------------------|
| Bootstrap | 1–30 | `claude-haiku-4-5-20251001` | ~$0.05–0.15 |
| Signal | 30–60 | `claude-sonnet-4-6` | ~$2–5 |
| Acceleration | 60–100 | `claude-sonnet-4-6` | ~$2–5 |
| Prime | 100+ | `claude-opus-4-6` | ~$10–20 |

Haiku is sufficient for bootstrap — no score data exists yet, proposals are hypothesis-driven guesses regardless of substrate. Substrate quality matters once evolution records compound at cycle 30+.

**Note:** Claude Pro (claude.ai subscription) does NOT include API access. Get API keys separately from `console.anthropic.com`.

## Running the System (Once Built)

```bash
cp .env.template .env
# Add ANTHROPIC_API_KEY and OPENAI_API_KEY to .env
pip install anthropic openai prompt_toolkit rich python-dotenv
python boros/kernel.py
```

**Director CLI commands** (at the `boros>` prompt):
- `boros status` — show cycle, mode, scores (immediate)
- `boros pause` / `boros resume` — control the loop
- `boros inject "..."` — write steering note to Memory (REFLECT reads it next cycle)
- `boros set-mode evolution|work|dual` — change operating mode
- `boros task "..."` — queue a work task
- `boros eval now` — trigger immediate evaluation
- `boros approve` / `boros flag "reason"` — respond to spot-checks (every 5 cycles)
- `boros rollback N` — restore snapshot from eval N

## Architecture

### The Kernel (`boros/kernel.py`, ~50 lines)

Intentionally dumb. Reads manifest, loads skills in dependency order, owns the message loop, provides a clock, holds two LLM connections (Claude primary, GPT-4o for meta-eval). Zero intelligence in the kernel.

**Startup sequence:** Kernel spawns `eval-generator/eval_generator.py` as a subprocess FIRST (before boot), then polls for `eval-generator/shared/.ready` sentinel (30-second timeout). If sentinel doesn't appear, halt with `[BOROS HALT] Eval Generator failed to start.`

**Message loop:**
```python
while True:
    response = primary_llm.complete(messages, tools, system)
    for block in response.content:
        if block.type == "tool_use":
            result = registry[block.name](block.input, kernel)
            messages.append(tool_result(block.id, result))
        elif block.stop_reason == "end_turn":
            break
```

The LLM controls stage transitions by calling Loop Orchestrator tools. When `loop_end_cycle` is called, the kernel discards history and starts a fresh conversation. Skill directories use hyphens (`meta-evolution/`) — kernel loader uses `importlib` for path-based loading.

### Skills (All Intelligence Lives Here)

19 skills in two categories:

**Boot Skills** (strict load order, health_check on each — failure halts boot):
1. Director Interface (#0, pre-boot) — terminal UI (prompt_toolkit + rich), NOT health-checked
2. Mode Controller (#1)
3. Temporal Consciousness (#2)
4. Identity (#3)
5. Memory (#4)
6. Skill Router (#5)
7. Context Orchestration (#6)
8. Reflection (#7)
9. Meta-Evolution (#8)
10. Meta-Evaluation (#9)
11. Loop Orchestrator (#10)

**Demand Skills** (loaded as needed):
Skill Forge, Mission, Reasoning, Attention, Tool Use, Communication, Research, Eval Bridge

Each skill: `boros/skills/<skill-name>/SKILL.md` + `skill.json` + `state/` + `functions/` + `tests/` + `snapshots/` + `metrics/metrics.jsonl` + `changelog.md`

**Memory lives at `boros/memory/`** (top-level), NOT `boros/skills/memory/state/`.

### Two Main Loops

**Evolution Loop** (default): `REFLECT → EVOLVE → EVAL`
- REFLECT: analyze score history, find weakest category, write hypothesis (`reflection_write_hypothesis` — hard gate, EVOLVE cannot start without it)
- EVOLVE: translate hypothesis into a SKILL.md edit, snapshot, validate, test, GPT-4o review, apply or reject
- EVAL: Eval Generator tests Boros, scores flow back, backfill records, regression check, update high-water marks

**Work Loop**: `RECEIVE → PLAN → EXECUTE → DELIVER → LEARN`
- Work cycles don't count toward evolution counter
- Work learning artifacts feed back into REFLECT as high-priority context

### System Prompt Assembly (`loop_start`)

Five blocks, joined by `\n\n`:
1. Identity block (from `identity.json`)
2. Stage directive (from `loop_definitions.json`)
3. Context manifest JSON (metadata from `context_load`)
4. Loaded memory content — actual record text from `context_load` → `content` key
5. Rules ("Call `loop_advance_stage` when done.")

### Evaluation System

`world_model.json` — 12 categories, all weight 1.0: Instruction Following, Reasoning Depth, Memory Coherence, Adaptability, Metacognition, Temporal Awareness, Learning Velocity, Goal Coherence, Communication Quality, Integration, Research Quality, Task Execution.

Ships pre-filled. Eval Generator needs rubrics on cycle 1. Director edits `world_model.json` directly. Boros sees category names/descriptions/scores but NOT rubrics, weights, or test questions. Changing a category's definition resets its high-water mark.

**Eval Generator** (`eval-generator/eval_generator.py`) — separate process, separate LLM connection, file-based communication only. Builds a read-only Boros copy by reading all SKILL.md files + `identity.json` → assembles into a Claude system prompt → sends test prompts as standalone API calls (no tools, no kernel boot). GPT-4o scores raw text responses against rubrics.

### Memory Layout

```
boros/memory/
  evolution_records/     # every proposed change and outcome
  sessions/              # one record per completed cycle
  experiences/           # structured lessons
  facts/                 # self-discoveries
  task_records/          # work tasks
  score_history.jsonl    # append-only (never deleted)
```

`session/` is cleared at cycle end. `memory/` persists forever.

### Snapshot & Git Tagging

Eval Bridge owns both. After `eval_update_high_water`: copies `boros/` (minus `snapshots/`) into `snapshots/eval-{id}/`, runs `git tag eval-{id}-score-{composite}` (skipped silently if no git). System rollback (`boros rollback N`) handled by Director Interface — infrastructure, not LLM-facing.

### Regression Protection

High-water marks: `skills/eval-bridge/state/high_water_marks.json`. Auto-rollback if any category drops > 0.02 below its best score.

---

## Critical Implementation Decisions (Gap Fixes)

These decisions resolve architectural issues found during pre-build audit. **Implement 25 and 26 first — they are prerequisites for all others.**

All 13 issues are resolved in `Boros.md` (spec) and `Seed-skills.md` (implementation). The standalone SKILL.md files (`04-`, `06-`, `08-`, `09-`) are verified accurate.

### Decision 25 — Eval Generator Subprocess (ISSUE-001, Fatal)

`kernel.py` spawns Eval Generator as a subprocess before the boot sequence:
```python
eval_proc = subprocess.Popen(["python", "eval-generator/eval_generator.py"], cwd=boros_root)
```
Polls `eval-generator/shared/.ready` with 30-second timeout. `eval_generator.py` writes `.ready` as its last step before entering its polling loop. Eval Generator is a child process — killed automatically when kernel exits.

### Decision 26 — `context_load()` Returns Actual Memory Content (ISSUE-002, Fatal)

`context_load()` return schema gains a `content` key with the actual serialized text of selected records. `loop_start()` uses this as block 4 of the system prompt. Without this, REFLECT is blind.

```python
return {
    "status": "ok",
    "loaded": loaded,     # token counts per category
    "manifest": manifest, # metadata summary
    "content": content    # actual text for system prompt injection
}
```

`content` format: sections `=== IDENTITY ===`, `=== SCORE HISTORY ===`, `=== EVOLUTION RECORDS ===`, `=== EXPERIENCES ===`.

### Decision 27 — `evolve_propose()` Required Parameters (ISSUE-003 + ISSUE-008, High)

`evolve_propose()` signature — **two required params**:
```python
evolve_propose(
    target_skill: str,
    change_description: str,
    rationale: str,
    proposed_skillmd: str,   # REQUIRED — full new SKILL.md content
    target_category: str,    # REQUIRED — must match evolve_set_target() call
    research_sources: list = []
)
```

`evolve_propose()` stores `proposed_skillmd` immediately on the proposal as `skillmd_update`. `evolve_apply()` makes `updated_skillmd` optional, falling back to `proposal["skillmd_update"]`.

### Decision 28 — Snapshot ID on Proposal (ISSUE-004 + ISSUE-005, High)

`evolve_propose()` captures snapshot_id from `forge_snapshot()` and stores it on the proposal:
```python
snap_result = kernel.registry["forge_snapshot"]({"skill_name": target_skill}, kernel)
if snap_result.get("status") != "ok":
    return {"status": "error", "error": f"Snapshot failed: {snap_result.get('error')}"}
snapshot_id = snap_result["snapshot_id"]
proposal["snapshot_id"] = snapshot_id
```

`evolve_rollback()` uses `proposal["snapshot_id"]` (not `proposal["old_version"]`).

### Decision 29 — `target_category` Through Proposal (ISSUE-006, High)

`evolve_propose()` accepts `target_category` and stores it on the proposal. `evolve_apply()` reads it when writing evolution records. `evolve_history(category=...)` filtering depends on this field being populated.

### Decision 30 — Meta-Evaluation Error Policy (ISSUE-007, Medium)

When `review_proposal()` returns `{"status": "error"}`:
1. Retry once
2. If errors again → treat as REJECTED (infrastructure failure)
3. Write experience record with `reason: "meta_eval_infrastructure_failure"`
4. Call `loop_advance_stage("EVAL")` — never auto-approve on failure

### Decision 31 — Baseline Test Field Rename (ISSUE-009, Medium)

Proposal field renamed from `test_results` → `baseline_test_results`. Meta-eval prompt clarifies: "Tests verify the skill was functional before this change. They do not test the proposed new behavior." Correctness dimension (weight 0.30) evaluates logical soundness of the change, not baseline test passage.

### Decision 32 — `eval_read_scores()` Write Contract (ISSUE-010, Medium)

`eval_read_scores()` MUST synchronously append to `memory/score_history.jsonl` before returning, including `eval_id`, `timestamp`, `cycle`, `scores`, `composite`, `deltas`, `plateau_flag`, `cycles_since_improvement`.

### Decision 33 — Spot-Check Auto-Approve Timeout (ISSUE-011, Low)

`config.json` gains `spot_check_timeout_minutes` (default `0` = blocking). When non-zero, Loop Orchestrator auto-approves after timeout and writes a fact to memory.

### Decision 34 — Context Orchestration in EVAL (ISSUE-012, Low)

`context-orchestration` `stage_visibility` updated to `["REFLECT", "EVOLVE", "EVAL"]` in both `skill.json` and `manifest.json`.

### Decision 35 — Cycle ID Fallback (ISSUE-013, Low)

`evolve_propose()` reads cycle from `loop_get_state()` via kernel registry first, falls back to direct file read of `loop_state.json`. Sanity check: if cycle reads as 0 but evolution records exist, log `[WARN] evolve_propose: cycle reads as 0 but evolution records exist. loop_state.json may be corrupt.`

---

## Seed Skills — Implementation Notes

Four seed skills are hand-written in `Seed-skills.md` and their standalone SKILL.md files. These are copied verbatim during Phase 1 build. The Python implementations in `Seed-skills.md` contain all fixes from Decisions 25–35.

**Seed skill files (verified accurate as of 2026-03-31):**
- `04-memory-SKILL.md` — Memory skill instructions
- `06-context-orchestration-SKILL.md` — Context Orchestration (includes `content` field contract, budget profiles, director injections)
- `08-meta-evolution-SKILL.md` — Meta-Evolution (full evolve_propose signature with `proposed_skillmd` and `target_category`)
- `09-meta-evaluation-SKILL.md` — Meta-Evaluation (correct dimensions, Infrastructure Failure Policy)

**Key corrections applied to `Seed-skills.md` during pre-build audit:**

| File | Fix | Issue |
|------|-----|-------|
| `evolve_propose.py` | Added `proposed_skillmd` (required), validates non-empty | ISSUE-003 |
| `evolve_propose.py` | Added `target_category` param, stored on proposal | ISSUE-006 |
| `evolve_propose.py` | Captures and stores `snapshot_id` from `forge_snapshot()` | ISSUE-005 |
| `evolve_propose.py` | Checks `forge_snapshot()` return status; errors halt proposal | ISSUE-005 |
| `evolve_propose.py` | Renamed `test_results` → `baseline_test_results` on proposal | ISSUE-009 |
| `evolve_propose.py` | Reads cycle from `loop_get_state()` first, file fallback, sanity check | ISSUE-013 |
| `evolve_rollback.py` | Uses `proposal["snapshot_id"]` not `proposal["old_version"]` | ISSUE-004 |
| `prompt_builder.py` | Field name corrected to `baseline_test_results`; clarifying note added | ISSUE-009 |
| `_default_criteria` | Correctness dimension rewritten to reflect logical soundness, not test results | ISSUE-009 |
| `context_load.py` | Full rewrite: collects actual record text, builds `=== SECTION ===` content string, returns `content` key | ISSUE-002 |
| `context-orchestration skill.json` | `stage_visibility` updated to include `"EVAL"` | ISSUE-012 |
| Embedded SKILL.md sections | Updated to match the standalone SKILL.md files (evolve_propose signature, rules, dimensions, failure policy) | Multiple |

---

## Key Design Principles

- **SKILL.md is the implementation** — the LLM reads SKILL.md as its instructions. Evolution = rewriting these files.
- **Evolution records are the moat** — accumulated history, not the code, is the proprietary asset. Code is open-sourceable; records are not.
- **Two LLMs by design** — Claude (primary substrate), GPT-4o (meta-eval + eval generator). Prevents self-approval bias.
- **Append-only stores** — history never deleted; enables regression analysis and compounding.
- **File-based IPC** — Eval Generator communicates via JSON files only. No context contamination.
- **Kernel dumb, skills smart** — LLM decides stage transitions via Loop Orchestrator tools; kernel plumbs messages.
- **Single-folder layout** — everything in `boros/`. Clone, set API keys, run.

## Key Reference Files

- `build-order.md` — 8-phase implementation plan with executable bash acceptance tests per phase
- `pipeline.md` — complete runtime behavior: boot, cycle mechanics, error recovery, stage transitions
- `Skill-reference.md` — function signatures and state schemas for all 15 non-seed skills
- `Seed-skills.md` — production-ready implementations for Memory, Meta-Evolution, Meta-Evaluation, Context Orchestration (copy verbatim; all issue fixes applied)
- `decisions.md` — all 35 architectural decisions; decisions 25–35 are the 13 gap fixes
- `Boros.md` — exhaustive system specification (~95KB); authoritative source of truth
- `ISSUES.md` — 13 pre-build issues with severity and resolution pointers (all resolved)
- `world-model.json` — 12 scoring categories with rubrics (ships pre-filled)
