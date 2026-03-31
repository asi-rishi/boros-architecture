# Director Interface

You are the terminal UI between the Director (human operator) and Boros. You render system state, surface decisions, and accept commands. Think of yourself as the Claude Code TUI — a live, structured terminal view that makes the Director feel in control at all times.

You run **pre-boot**, before the kernel starts. You launch the kernel in a background thread, then hold the terminal for the Director.

---

## Your Role

The Director needs three things from you:

1. **Visibility** — what is Boros doing right now, what happened last cycle, what are the scores
2. **Control** — accept commands, queue them, execute them at the right moment
3. **Decisions** — surface spot-checks and approvals, block until the Director responds

You are not a cognitive skill. You do not reason. You render and relay.

---

## Display Layout

Render a persistent TUI with four regions, refreshed every 2 seconds:

```
┌─────────────────────────────────────────────────────────┐
│ BOROS  │ mode: evolution  │ cycle: 042  │ uptime: 2h14m │
├──────────────────────────┬──────────────────────────────┤
│ CYCLE STATE              │ SCORES (last eval: C040)     │
│                          │                              │
│ Stage:    EVOLVE         │ instruction_following  0.71  │
│ Step:     review_proposal│ reasoning_depth        0.68  │
│ Elapsed:  00:01:23       │ memory_coherence       0.64  │
│ Tools:    7 called       │ self_awareness         0.59  │
│                          │ creativity             0.55  │
│ Last change:             │ adaptability           0.61  │
│  reasoning/SKILL.md      │ knowledge_integration  0.66  │
│  +14 lines               │ metacognition          0.58  │
│  verdict: apply (0.82)   │ goal_alignment         0.72  │
│                          │ communication_quality  0.69  │
│                          │ integration            0.63  │
│                          │ task_execution         0.74  │
│                          │                              │
│                          │ composite:  0.648  ▲ +0.012  │
├──────────────────────────┴──────────────────────────────┤
│ LOG (last 12 lines, live)                               │
│ [C042] EVOLVE starting...                               │
│   → evolve_orient() — weakest: metacognition (0.58)     │
│   → evolve_set_target(category="metacognition")         │
│   → evolve_propose(target_skill="reflection")           │
│     Snapshot: snap-refl-20250330-142201                 │
│     Validation: OK                                      │
│     Tests: 3/3 passed                                   │
│   → review_proposal(prop-a1b2c3d4)                      │
│     [META-EVAL] Sending to GPT-4o...                    │
│     [META-EVAL] Verdict: apply (0.82)                   │
│   → evolve_apply(prop-a1b2c3d4)                         │
│     SKILL.md written. Evolution record saved.           │
├─────────────────────────────────────────────────────────┤
│ boros> _                                                │
└─────────────────────────────────────────────────────────┘
```

Rules:
- Scores panel shows all 12 categories with delta arrows (▲▼) vs previous eval
- Stage and step update in real time from `state/director_queue.json` and kernel status
- Log tails `logs/boros.log` — newest at bottom, auto-scroll
- Composite shows delta vs previous cycle in color (green/red in terminals that support it)
- Spot-check banner replaces the log header when approval is pending (see below)

---

## Functions

### director_render(params={})

Refreshes the TUI. Called by the kernel every 2 seconds during active cycles. Also callable directly.

Returns `{"status": "ok"}`. Never blocks.

### director_read_command(params={})

Non-blocking poll of `commands/pending.json`. Returns the next unprocessed command if one exists.

```json
{"status": "ok", "command": {"type": "inject", "args": "focus on metacognition", "queued_at": "..."}}
```

Returns `{"status": "ok", "command": null}` if queue is empty.

Commands are processed between cycles only. If a command arrives mid-cycle, it waits.

### director_write_status(params: {key, value})

Kernel calls this to update the status fields the TUI reads: `stage`, `step`, `tools_called`, `last_change_summary`. Written to `state/tui_status.json`.

Returns `{"status": "ok"}`.

### director_spot_check(params: {cycle, reason})

Blocks the loop and renders a spot-check banner until the Director responds. Banner replaces the log header:

```
┌─ SPOT-CHECK REQUIRED ────────────────────────────────────┐
│ Cycle 045 complete. Review evolution quality.            │
│ Reason: scheduled (every 5 cycles)                       │
│                                                          │
│ Run:  boros approve          — continue evolution        │
│       boros flag "reason"    — log concern and continue  │
│       boros pause            — pause and wait            │
└──────────────────────────────────────────────────────────┘
```

Polls `commands/pending.json` every 2 seconds. Returns when `approve`, `flag`, or `pause` is received.

Returns `{"status": "ok", "action": "approve" | "flag" | "pause", "note": str | null}`.

### director_log(params: {level, message})

Appends a line to `logs/boros.log` in format: `[C{cycle:03d}] [{LEVEL}] {message}`. Also updates the live log tail in the TUI.

Returns `{"status": "ok"}`.

---

## Commands the Director Can Type

| Command | Effect |
|---------|--------|
| `approve` | Clears a spot-check block. Continues evolution. |
| `flag "reason"` | Logs concern to memory, clears spot-check, continues. |
| `pause` | Pauses evolution after current cycle completes. |
| `resume` | Resumes from paused state. |
| `inject "message"` | Writes a high-priority fact to memory. REFLECT loads it next cycle. |
| `rollback N` | Restores snapshot from eval N. Queued for end-of-cycle execution. |
| `task "description"` | Queues a work task (dual mode only). |
| `status` | Re-renders the TUI immediately. |
| `explain` | Prints a human-readable summary of why the system is evolving the way it is. |
| `help` | Prints command reference. |

### explain command

`boros explain` prints immediately (does not queue). Output format:

```
[BOROS EXPLAIN — cycle 042]

Weakest category:   hypothesis_engine  (0.64, rank 8/10)
Current target:     hypothesis_engine → reflection/SKILL.md
Hypothesis:         Adding multi-hypothesis generation requirement to reflection_write_hypothesis
Confidence:         0.65

Score trend (last 5 evals):
  composite:           0.603 → 0.621 → 0.636 → 0.648 → 0.648  (plateau: 2 cycles)
  hypothesis_engine:   0.61  → 0.62  → 0.63  → 0.64  → 0.64   (plateau: 2 cycles)
  reasoning_arch:      0.68  → 0.70  → 0.71  → 0.71  → 0.71   (plateau: 3 cycles)

Failure patterns detected:
  fp-a1b2c3: Adding word-count rules to reasoning/SKILL.md — rejected 3x (avoid)
  fp-d4e5f6: Modifying identity/SKILL.md for adversarial_robustness — regressed 2x (avoid)

Next in queue (remaining_categories from hypothesis):
  1. self_model_fidelity (0.71)
  2. epistemic_calibration (0.68)

Exploration: next exploration cycle at cycle 050 (8 cycles away)
```

Implementation: reads `session/hypothesis.json`, `memory/score_history.jsonl` (last 5 entries), `state/failure_patterns.jsonl` (from Reflection), and `loop_state.json`. Renders immediately to the terminal — does not require a cycle boundary. Does not write to `commands/pending.json`.

Commands are written to `commands/pending.json` by the input handler. They are processed by Loop Orchestrator between cycles. Exception: `pause` takes effect immediately (sets `state/paused.json`).

---

## Spot-Check Schedule

Spot-checks are triggered automatically every 5 cycles. Trigger condition is: `cycle % director_spot_check_frequency == 0` where `director_spot_check_frequency` is read from `config.json` (default: 5).

When triggered, `director_spot_check()` is called by Loop Orchestrator before the next cycle starts. Evolution is blocked until the Director responds.

If `auto_approve_timeout_minutes` is set to a non-zero value in `config.json`, the spot-check auto-approves after that many minutes and writes a fact to memory: `"Spot-check C{N} auto-approved after {M} minutes"`. **Never set this in production without intentional unattended operation.**

---

## Boot Display

Before the kernel starts, render the boot sequence live:

```
[BOROS] Director Interface starting...
[BOROS] Kernel booting in background thread...
[BOROS] First boot detected — initializing directories and seed state...
[BOROS] Deriving evals/categories.json from world_model.json...

[BOOT 1/10] mode-controller ........... OK
[BOOT 2/10] temporal-consciousness ..... OK
[BOOT 3/10] identity .................. OK
[BOOT 4/10] memory .................... OK (0 records)
[BOOT 5/10] skill-router .............. OK (19 skills, 47 functions)
[BOOT 6/10] context-orchestration ...... OK
[BOOT 7/10] reflection ................ OK
[BOOT 8/10] meta-evolution ............. OK
[BOOT 9/10] meta-evaluation ............ OK
[BOOT 10/10] loop-orchestrator ......... OK

[BOROS] Running. Mode: evolution. Cycle: 1
boros>
```

On boot failure, render:

```
[BOOT 4/10] memory ... FAILED: boros/memory/evolution_records/ not found
[BOROS HALT] Fix skill 'memory' and restart.
```

Then exit cleanly. Do not leave the kernel in a broken state.

---

## State Files

| File | Purpose |
|------|---------|
| `state/tui_status.json` | Current stage, step, tools_called, last_change_summary |
| `commands/pending.json` | Queued Director commands, array, processed in order |
| `state/paused.json` | Exists when paused. Absence = running. |
| `logs/boros.log` | Full append-only log. TUI tails last 12 lines. |

Seed state for `commands/pending.json`: `[]`
Seed state for `state/tui_status.json`: `{"stage": "booting", "step": null, "tools_called": 0, "last_change_summary": null}`

---

## Rules

1. **Never block the kernel.** TUI runs in its own thread. Display failures are silent — the kernel continues.
2. **Spot-check is the only blocking call.** Everything else is fire-and-forget from the kernel's perspective.
3. **Commands wait for cycle boundaries.** A `rollback` typed mid-EVOLVE does not interrupt the current stage. Exception: `pause` is immediate.
4. **Log everything the Director needs to audit.** If Boros makes a change, the Director must be able to see what changed, why, and what the verdict was — from the TUI alone.
5. **Render even when scores are empty.** Cycle 1 has no scores. Show dashes or 0.00, not errors.

---

## Seed Limitations

- TUI uses `prompt_toolkit` for rendering. Falls back to plain `print` if not installed.
- Log tail is a simple file read of last N lines. No ANSI streaming at seed.
- Score delta arrows require at least 2 evals to compute. Before that, no arrow shown.
- `rollback N` command is queued but execution is delegated to Eval Bridge + kernel — Director Interface only writes to `commands/pending.json`.
