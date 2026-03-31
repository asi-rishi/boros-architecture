.

---

## 1. Director Interface (Skill #0 — Pre-boot)

**Type:** Pre-boot (not part of health-check sequence)
**Purpose:** Terminal UI for the Director. Wraps the kernel in a background thread.
**Dependencies:** None (loads before everything)

**Implementation:** `prompt_toolkit` based terminal. Kernel runs in background thread. Foreground: readline input for Director commands. Background: streams `logs/cycles.log` to terminal. Ctrl+C sets `pause_requested` flag, loop stops at cycle boundary.

**Functions:**

- `director_start()` — Launches terminal UI, starts kernel in background thread
- `director_parse_command(input: str)` — Parses input into command + args
- `director_dispatch(command: str, args: str)` — Routes to immediate execution or writes to `commands/pending.json`
- `director_status()` — Immediate: reads loop_state.json + high_water_marks.json + last scores, prints inline

**Command routing:**

- Immediate: `status`
- Queued (write to `commands/pending.json`): `pause`, `resume`, `inject`, `set-mode`, `task`, `eval now`, `approve`, `flag`, `rollback`

**State files:** None (writes to `commands/pending.json`)
**Note:** This is NOT an LLM-facing skill. No SKILL.md needed. Pure Python terminal application.

---

## 2. Mode Controller (Boot #1)

**Type:** Boot
**Purpose:** Gets and sets the operating mode (evolution, work, dual).
**Dependencies:** None

**Functions:**

- `mode_get(params={}) → {"status": "ok", "mode": str}` — Reads mode from manifest.json
- `mode_set(params: {mode: str}) → {"status": "ok", "mode": str}` — Validates mode is one of [evolution, work, dual], writes to manifest.json

**health_check:** `mode_get` — verifies mode is valid
**State files:** None (reads/writes manifest.json)
**Stage visibility:** REFLECT, EVOLVE, EVAL

---

## 3. Temporal Consciousness (Boot #2)

**Type:** Boot
**Dependencies:** Mode Controller
**Purpose:** Time awareness. Clock, elapsed time, cycle timing.

**Functions:**

- `time_now(params={}) → {"status": "ok", "timestamp": str}` — Returns UTC ISO timestamp via `kernel.clock()`
- `time_elapsed_since(params: {timestamp: str}) → {"status": "ok", "seconds": float}` — Seconds since given timestamp
- `time_cycle_started(params={}) → {"status": "ok", "started_at": str, "elapsed_seconds": float}` — Reads from loop_state.json
- `time_estimate_remaining(params: {budget_minutes: int}) → {"status": "ok", "remaining_seconds": float}` — Budget minus elapsed

**health_check:** `time_now`
**State files:** `state/cycle_times.jsonl` — append-only log of cycle durations
**Stage visibility:** REFLECT, EVOLVE, EVAL

---

## 4. Identity (Boot #3)

**Type:** Boot
**Dependencies:** Mode Controller
**Purpose:** Boros's sense of self. Name, purpose, self-narrative.

**Functions:**

- `identity_read(params={}) → {"status": "ok", "identity": dict}` — Reads state/identity.json
- `identity_update(params: {field: str, value: any}) → {"status": "ok"}` — Updates a field in identity.json

**health_check:** `identity_read`
**State files:** `state/identity.json`
**Seed state:**

```json
{
  "name": "Boros",
  "purpose": "Self-improving AI system. Evolve skills, raise scores, reach Prime Boros.",
  "model_name": "ARES",
  "substrate": "claude-sonnet-4-20250514",
  "created": "ISO-8601",
  "self_narrative": ""
}
```

**Stage visibility:** REFLECT, EVOLVE, EVAL

---

## 5. Skill Router (Boot #5)

**Type:** Boot
**Dependencies:** Mode Controller
**Purpose:** Controls which tools the LLM sees at each stage. Tracks token budget for tools.

**Functions:**

- `router_get_tools(params: {stage: str}) → {"status": "ok", "tools": list[dict]}` — Returns JSON Schema tool definitions for all functions visible at this stage. Reads `stage_visibility` from each skill's skill.json + any overrides in `state/routing_rules.json`.
- `router_get_budget(params={}) → {"status": "ok", "tool_tokens": int, "tool_count": int}` — Estimates total tokens consumed by current tool definitions.
- `router_register_demand(params: {skill_name: str}) → {"status": "ok"}` — Loads a demand skill into the active tool set for the current cycle.
- `router_unregister_demand(params: {skill_name: str}) → {"status": "ok"}` — Removes a demand skill from the active set.

**health_check:** `router_get_tools` with stage="REFLECT"
**State files:** `state/routing_rules.json` — seed: empty `{}`, Boros can evolve overrides
**Stage visibility:** REFLECT, EVOLVE, EVAL

---

## 6. Reflection (Boot #7)

**Type:** Boot
**Dependencies:** Mode Controller, Memory
**Purpose:** Analyzes scores and evolution records. Writes the hypothesis that drives EVOLVE.

**Functions:**

- `reflection_analyze(params={}) → {"status": "ok", "analysis": dict}` — Reads scores, evolution records, experiences. Returns weakest categories, patterns, repeated failures.
- `reflection_write_hypothesis(params: {hypothesis_data: dict}) → {"status": "ok", "hypothesis_id": str}` — Writes structured plan to `session/hypothesis.json`. **MUST be called before EVOLVE can start.** Loop Orchestrator hard-gates on this.
- `reflection_read_hypothesis(params={}) → {"status": "ok", "hypothesis": dict}` — Reads from session/hypothesis.json.

**Hypothesis schema:**

```json
{
  "cycle": 42,
  "hypothesis_id": "hyp-042-001",
  "score_snapshot": { "reasoning_depth": 0.71 },
  "pattern_analysis": "string",
  "target_category": "memory_coherence",
  "target_skill": "memory",
  "hypothesis": "Adding keyword indexing should improve retrieval precision",
  "confidence": 0.72,
  "fallback": "Try reducing context load size if indexing doesn't help",
  "remaining_categories": ["reasoning_depth", "adaptability"]
}
```

**State files:** `state/analysis_history.jsonl`
**Stage visibility:** REFLECT

---

## 7. Loop Orchestrator (Boot #10)

**Type:** Boot
**Dependencies:** Mode Controller (loaded last in boot sequence)
**Purpose:** Runs the loop. Manages stage transitions, cycle counting, conversation lifecycle.

**Functions:**

- `loop_start(params: {mode: str}) → {"status": "ok"}` — Called after boot. Builds system prompt from: identity block, stage directive, context manifest, loaded memory, rules. Stage directives stored in `loop_definitions.json`, evolvable. Starts first LLM conversation, begins first cycle.
- `loop_advance_stage(params: {current_stage: str}) → {"status": "ok", "next_stage": str}` — Moves to next stage. Swaps tools via Skill Router. Updates stage directive. **Hard gate:** EVOLVE cannot start until `session/hypothesis.json` exists.
- `loop_end_cycle(params={}) → {"status": "ok", "cycle": int}` — Ends cycle, increments counter, signals kernel to discard conversation history and start fresh, clears `session/`, polls `commands/pending.json`.
- `loop_get_state(params={}) → {"status": "ok", "cycle": int, "stage": str, "mode": str, "started_at": str}` — Returns current state.

**State files:**

- `state/loop_state.json` — seed: `{"cycle": 0, "stage": null, "mode": "evolution", "cycle_started_at": null, "total_cycles_completed": 0}`
- `state/loop_definitions.json` — seed:
```json
{
  "evolution": ["REFLECT", "EVOLVE", "EVAL"],
  "work": ["RECEIVE", "PLAN", "EXECUTE", "DELIVER", "LEARN"],
  "stage_directives": {
    "REFLECT": "Analyze your scores and evolution records. Identify the weakest category. Write a hypothesis by calling reflection_write_hypothesis. Call loop_advance_stage when done.",
    "EVOLVE": "Load your hypothesis. Propose a targeted change to a skill's SKILL.md. Send it for review via review_proposal. If approved, apply it via evolve_apply. Call loop_advance_stage when done.",
    "EVAL": "Request an evaluation via eval_request. When scores arrive, backfill records, check regressions, and update high-water marks. Call loop_end_cycle when done.",
    "RECEIVE": "Parse the task requirements. Identify any ambiguity. Call loop_advance_stage when ready to plan.",
    "PLAN": "Break the task into steps. Query Memory for similar past tasks. Call loop_advance_stage when ready to execute.",
    "EXECUTE": "Do the work. Use Tool Use for terminal, HTTP, and file operations. Call loop_advance_stage when done.",
    "DELIVER": "Package and deliver the results via the Communication skill. Call loop_advance_stage when done.",
    "LEARN": "Write structured learning artifacts — gap reports, performance patterns, technique discoveries. Tag them work_learning. Call loop_end_cycle when done."
  }
}
```

**Stage visibility:** REFLECT, EVOLVE, EVAL

---

## 8. Skill Forge (Demand)

**Type:** Demand
**Purpose:** Safety layer for skill modifications. Snapshots, validates, tests, applies, rolls back.

**Functions:**

- `forge_snapshot(params: {skill_name: str}) → {"status": "ok", "snapshot_id": str}` — Saves current skill state to `skills/{name}/snapshots/`.
- `forge_validate(params: {skill_name: str}) → {"status": "ok" | "error", "errors": list}` — Checks SKILL.md exists, skill.json valid, functions importable.
- `forge_test(params: {skill_name: str}) → {"status": "ok", "total": int, "passed": int, "failed": int, "failures": list}` — Runs `pytest` on the skill's test suite.
- `forge_apply_diff(params: {skill_name: str, diff: str}) → {"status": "ok"}` — Writes approved change to SKILL.md.
- `forge_rollback(params: {skill_name: str, snapshot_id: str}) → {"status": "ok"}` — Restores from snapshot.
- `forge_create_skill(params: {spec: dict}) → {"status": "ok", "skill_id": str}` — Creates full directory structure from spec.

**Stage visibility:** EVOLVE

---

## 9. Mission (Demand)

**Type:** Demand
**Purpose:** Holds Boros's current goals and priorities.

**Functions:**

- `mission_read(params={}) → {"status": "ok", "mission": dict}` — Reads state/mission.json
- `mission_update(params: {goals: dict}) → {"status": "ok"}` — Writes updates

**State files:** `state/mission.json` — seed: `{"goals": [], "priorities": [], "constraints": []}`
**Stage visibility:** REFLECT, EVOLVE

---

## 10. Reasoning (Demand)

**Type:** Demand
**Purpose:** Structured thinking tools.

**Functions:**

- `reason_decompose(params: {problem: str}) → {"status": "ok", "sub_problems": list}` — Breaks problem into parts
- `reason_evaluate_options(params: {options: list, criteria: list}) → {"status": "ok", "rankings": list}` — Scores options against criteria
- `reason_check_logic(params: {argument: str}) → {"status": "ok", "gaps": list, "contradictions": list}` — Finds logical issues

**Stage visibility:** REFLECT, EVOLVE, EVAL, PLAN, EXECUTE

---

## 11. Attention (Demand)

**Type:** Demand
**Purpose:** Manages focus within a cycle. Prioritizes information.

**Functions:**

- `attention_prioritize(params: {items: list, context: str}) → {"status": "ok", "ranked": list}` — Ranks items by relevance
- `attention_flag(params: {item: str, reason: str}) → {"status": "ok"}` — Flags something as important

**Stage visibility:** REFLECT, EVOLVE

---

## 12. Tool Use (Demand)

**Type:** Demand
**Purpose:** Interface for external tools.

**Functions:**

- `tool_terminal(params: {command: str}) → {"status": "ok", "stdout": str, "stderr": str, "returncode": int}` — Runs shell command (subprocess with timeout)
- `tool_http(params: {method: str, url: str, body: dict?}) → {"status": "ok", "status_code": int, "body": str}` — HTTP request
- `tool_file_read(params: {path: str}) → {"status": "ok", "content": str}` — Read file
- `tool_file_write(params: {path: str, content: str}) → {"status": "ok"}` — Write file

**Stage visibility:** EXECUTE

---

## 13. Communication (Demand)

**Type:** Demand
**Purpose:** Formats and delivers outputs.

**Functions:**

- `comm_format(params: {content: str, audience: str, style: str}) → {"status": "ok", "formatted": str}` — Adapts content
- `comm_respond(params: {message: str}) → {"status": "ok"}` — Delivers response

**Stage visibility:** DELIVER

---

## 14. Research (Demand)

**Type:** Demand
**Purpose:** Finds and evaluates external information.

**Functions:**

- `research_search(params: {query: str}) → {"status": "ok", "results": list}` — Web search (at seed: stub returning empty)
- `research_evaluate(params: {source: str}) → {"status": "ok", "credibility": float, "assessment": str}` — Source evaluation
- `research_synthesize(params: {sources: list, question: str}) → {"status": "ok", "synthesis": str}` — Combines sources

**Stage visibility:** REFLECT, EVOLVE, PLAN, EXECUTE

---

## 15. Eval Bridge (Demand)

**Type:** Demand
**Purpose:** Only connection between Boros and the external Eval Generator. File-based communication.

**Functions:**

- `eval_request(params={}) → {"status": "ok", "request_id": str}` — Writes request file to `eval-generator/shared/requests/`. Polls `eval-generator/shared/results/` for result. Timeout: 10 minutes.
- `eval_read_scores(params={}) → {"status": "ok", "scores": dict, "composite": float}` — Reads latest scores from result file.
- `eval_backfill(params: {scores: dict}) → {"status": "ok", "records_updated": int}` — Fills `post_scores` on all pending evolution records via `memory_update`. Computes deltas.
- `eval_check_regression(params: {scores: dict}) → {"status": "ok", "regressions": list, "rollback_triggered": bool}` — Compares against high-water marks. Any category below high-water minus 0.02 triggers rollback via `evolve_rollback`.
- `eval_update_high_water(params: {scores: dict}) → {"status": "ok", "updated": list}` — Updates high-water marks for new bests. After updating, triggers system snapshot (internal helper) and git tag (`eval-{id}-score-{composite}`). Git tag skipped silently if git not initialized.

**State files:** `state/high_water_marks.json` — seed: all 12 categories at 0.0
**Stage visibility:** EVAL

---

## End

_Generate full implementations for all 15 skills. Each function follows `def func(params: dict, kernel=None) -> dict`. Write SKILL.md files following seed skill patterns. Every function must handle errors gracefully — return `{"status": "error", "error": str}`, never raise uncaught exceptions._
