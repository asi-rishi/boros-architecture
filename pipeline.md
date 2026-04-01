  ---

## 1. Boot Sequence

```
$ python boros/kernel.py

[BOROS] Director Interface starting...
[BOROS] Kernel booting in background thread...
[BOROS] First boot detected — initializing directories and seed state...
[BOROS] Deriving evals/categories.json from world_model.json...

[BOOT 1/10] mode-controller ... OK
[BOOT 2/10] temporal-consciousness ... OK
[BOOT 3/10] identity ... OK
[BOOT 4/10] memory ... OK (0 records, 0 experiences)
[BOOT 5/10] skill-router ... OK (19 skills registered, 47 functions)
[BOOT 6/10] context-orchestration ... OK
[BOOT 7/10] reflection ... OK
[BOOT 8/10] meta-evolution ... OK
[BOOT 9/10] meta-evaluation ... OK
[BOOT 10/10] loop-orchestrator ... OK

[BOROS] Running. Mode: evolution. Cycle: 1
boros>
```

**What happens mechanically:**

1. `kernel.py` launches Director Interface (skill #0) — sets up prompt_toolkit and rich terminal
2. Director Interface starts the kernel in a background thread
3. Kernel detects first boot (no `session/current_cycle.json`): creates all directories, writes seed state files, derives `evals/categories.json` from `world_model.json`
4. Kernel loads boot skills 1-10 in strict order, running `health_check()` on each
5. Any health_check failure = halt. Fix and restart. No partial boot.
6. Loop Orchestrator calls `loop_start()` — first cycle begins

**If boot fails:**
```
[BOOT 4/10] memory ... FAILED: boros/memory/evolution_records/ not found
[BOROS HALT] Fix skill 'memory' and restart.
```

---

## 2. Evolution Cycle (REFLECT → EVOLVE → EVAL)

### REFLECT

```
[C001] REFLECT starting...
  → context_load() fires — loads identity, scores (empty), evolution records (empty)
  → LLM reads context manifest — knows what's loaded
  → LLM calls reflection_analyze() — returns empty analysis (no scores yet)
  → LLM calls reflection_write_hypothesis() — writes first hypothesis
  → hypothesis.json written to session/
[C001] REFLECT done (4.1s)
```

**Mechanics:**

1. Context Orchestration fires (`context_load`) — builds context window per budget profile
2. Skill Router provides entire unbounded global toolset
3. LLM API call with system prompt + minimal working core + ALL tools
4. LLM reasons about scores and patterns, calls `reflection_analyze()`
5. LLM must call `reflection_write_hypothesis()` — **hard gate**, EVOLVE cannot start without it
6. If hypothesis doesn't exist after REFLECT, one retry. Still missing = cycle logged as failed, fresh cycle starts.

### EVOLVE

```
[C001] EVOLVE starting...
  → (All tools remain globally available, stage advancement merely updates system core status)
  → LLM loads hypothesis from session/hypothesis.json
  → LLM calls evolve_orient() — no scores yet, returns guidance
  → LLM calls evolve_set_target(category="self_model_fidelity", delta=0.05)
  → LLM calls evolve_propose(target_skill="reasoning", change_description="...", rationale="...", proposed_skillmd="...", target_category="self_model_fidelity")
    → Skill Forge: snapshot taken → validation passed → tests passed (0 tests)
    → Proposal saved: prop-a1b2c3d4e5f6
  → LLM calls review_proposal(proposal_id="prop-a1b2c3d4e5f6")
    → [META-EVAL] Sending diff to GPT-4o... (blocking)
    → [META-EVAL] Verdict: apply (weighted_total: 0.82, threshold: 0.55)
  → LLM calls evolve_apply(proposal_id="prop-a1b2c3d4e5f6")
    → SKILL.md written → version bumped → evolution record saved (post_scores=null)
[C001] EVOLVE done — 1 change applied (8.3s)
```

**Mechanics:**

1. LLM continues reasoning with the global unbounded toolset
2. Conversation history carries forward from REFLECT
3. LLM loads hypothesis from session state
4. Per proposal:
   - `evolve_propose()` → Skill Forge snapshots + validates + tests → proposal saved
   - `review_proposal()` → diff sent to GPT-4o (synchronous, blocking) → verdict returned
   - If "apply" → `evolve_apply()` writes SKILL.md + evolution record
   - If "apply_with_modifications" → LLM revises, calls `review_modify()` (max 3 rounds)
   - If "reject" → logged, failure experience written, next proposal
5. Cycles 1-20: exactly one proposal. After cycle 20: loop until all 10 categories addressed or budget approached.

### EVAL

```
[C001] EVAL starting...
  → eval_request() writes request file to eval-generator/shared/requests/
  → Eval Generator picks up request...
  → Eval Generator boots read-only Boros copy...
  → Eval Generator sends 3 test prompts per category (30 total)...
  → Eval Generator scores responses against rubrics...
  → Result file written to eval-generator/shared/results/
  → eval_read_scores() — scores received
  → eval_backfill() — evolution records updated with post_scores
  → eval_check_regression() — no regressions (first eval)
  → eval_update_high_water() — 10 high-water marks set
  → System snapshot saved to snapshots/eval-001/
  → Git tag: eval-001-score-0.57
[C001] Composite: 0.57
[C001] Cycle complete.
```

**Mechanics:**

1. Eval Bridge writes request file
2. Eval Generator (separate process) picks up, generates tests, boots read-only Boros, scores responses
3. Eval Bridge polls for result (timeout: 10 minutes)
4. On scores received:
   - Write to `memory/score_history.jsonl`
   - Backfill all pending evolution records with `post_scores` + deltas
   - Check regressions against high-water marks (threshold: best - 0.02)
   - Update high-water marks for new bests
   - System snapshot (full boros/ backup minus snapshots/ itself)
   - Git tag

### Cycle End

```
  → Conversation history discarded
  → session/ directory cleared
  → commands/pending.json polled and processed
  → Next cycle starts
```

---

## 3. Director Intervention Points

### Between Cycles (commands/pending.json)

| When                    | Command                                                  | What Happens                                                                 |
| ----------------------- | -------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Scores drifting         | `boros inject "focus on reasoning depth"`                | Written to Memory. REFLECT loads at high priority next cycle.                |
| Bad eval quality        | `boros flag "tests too easy for epistemic_calibration"`  | Written to Memory. Boros adjusts strategy.                                   |
| Everything fine         | `boros approve`                                          | Clears spot-check block.                                                     |
| Stuck in loop           | `boros pause` → edit `world_model.json` → `boros resume` | Category definitions updated, high-water marks reset for changed categories. |
| Catastrophic regression | `boros rollback N`                                       | Restores snapshot from eval N, resets cycle counter.                         |

### Every 5 Cycles — Spot-Check

```
[C005] Spot-check due. Run: boros approve  or  boros flag "reason"
boros> approve
[C005] Spot-check approved. Continuing.
```

Director reviews: Are the proposals making sense? Are the evals testing the right things? Is Boros improving or thrashing?

### World Model Updates

Director edits `world_model.json` directly. Changes take effect next cycle. Changing a category's definition resets its high-water mark.

---

## 4. Work Cycle (RECEIVE → PLAN → EXECUTE → DELIVER → LEARN)

Active in `work` or `dual` mode.

```
boros> task "Write a Python script to parse CSV files"

[C025] WORK CYCLE — task received
  → RECEIVE: Parse requirements, identify ambiguity, load relevant context
  → PLAN: Break into steps, estimate effort, query Memory for similar past tasks
  → EXECUTE: Write code using Tool Use (tool_terminal, tool_file_write)
  → DELIVER: Package results via Communication skill
  → LEARN: Write gap_report, performance_pattern, or technique_discovery
    → Tagged "work_learning" → stored in tasks/learning/
[C025] Work cycle complete. (does NOT count toward evolution counter)
```

**Dual mode logic:** Director task in queue → work cycle. No task → evolution cycle.

**Feedback to evolution:** REFLECT loads unread `work_learning` artifacts at high priority. Real-world failures become evolution targets.

---

## 5. Error Recovery

| Error                        | What Happens                                                                   | Result                               |
| ---------------------------- | ------------------------------------------------------------------------------ | ------------------------------------ |
| Function error               | Caught, returned to LLM as tool error. LLM retries, works around, or moves on. | Cycle continues                      |
| Max tool calls (100)         | Cycle ends, next starts                                                        | Logged as budget-exceeded            |
| Cycle timeout (10 min)       | Cycle killed                                                                   | Logged as failed, fresh cycle starts |
| Cycle crash                  | Kernel logs failure                                                            | Fresh cycle starts                   |
| Eval timeout (10 min)        | Eval skipped                                                                   | Logged, next cycle starts            |
| Health check failure at boot | Halt                                                                           | Fix and restart                      |

**A single bad cycle never stops evolution.**

---

## 6. The Compounding Mechanism

```
Cycle 1-9:  REFLECT has no score data. Proposals are hypothesis-driven guesses.
Cycle 10:   First EVAL. Scores arrive. Evolution records backfilled with post_scores.
Cycle 11+:  REFLECT reads backfilled records. Sees: "change to reasoning/SKILL.md
            correlated with +0.03 on self_model_fidelity." Hypothesis quality improves.
Cycle 30+:  REFLECT has 20+ data points. Can identify: which skills affect which
            categories, which types of changes succeed, which fail repeatedly.
Cycle 100+: Dense pattern history. Proposals are precisely targeted. Random walk
            becomes directed evolution.
```

**Evolution records are the moat.** They compound. The codebase does not.

---

## 7. Timeline to Prime Boros

| Phase              | Cycles | What's Happening                                                                | Director Role                                         |
| ------------------ | ------ | ------------------------------------------------------------------------------- | ----------------------------------------------------- |
| Bootstrap          | 1-10   | No score data. Hypothesis-only proposals. First eval at cycle 10.               | Spot-check every 5. Use `inject` to nudge.            |
| Signal acquisition | 10-30  | First scores. Backfilled records. Compounding starts.                           | Spot-check. Flag bad evals. Adjust rubrics if needed. |
| Acceleration       | 30-60  | Dense history. Targeted proposals. Multiple proposals per cycle.                | Step back. Monitor composite trajectory.              |
| Plateau approach   | 60-100 | Marginal gains slow. Difficulty scaling kicks in. Substrate ceiling approached. | Monitor. Consider model upgrade (Sonnet → Opus).      |
| Prime              | 100+   | Composite ~0.85+ at Level 4 difficulty. All categories near ceiling.            | Fork into domain specialists.                         |

**Estimated cost:** ~$0.05-0.15 per cycle (Haiku, cycles 1-30). ~$2-5 per cycle (Sonnet, cycles 30-100). ~$10-20 per cycle (Opus, 100+). Change model in `manifest.json` → `llm.primary.model` — takes effect next cycle. API keys from `console.anthropic.com` (separate from Claude Pro subscription).

---

## 8. Domain Fork Procedure

1. Clone Prime Boros directory
2. Add domain-specific categories to `world_model.json` (on top of the 10 general ones)
3. Write domain rubrics with real-world anchors
4. `python boros/kernel.py` — fork inherits all general high-water marks
5. Evolution pressure now includes domain-specific categories
6. Domain expertise accumulates while general capability is maintained

---

## End

_Boot → REFLECT → EVOLVE → EVAL → repeat. The kernel loads skills. Skills do everything. The World Model says what "better" means. Evolution records remember what worked. The Director holds the safety net. Everything else, Boros earns._
