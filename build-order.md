BOROS — Build Order

> **For Claude Code.** Build in this exact sequence. Each phase must pass its acceptance criteria before proceeding. Do not skip ahead.

---

## Phase 1 — Skeleton

**Create:**

- `boros/__init__.py` — empty (required for package imports)
- `boros/kernel.py` — ~50 line bootstrap (read manifest, load skills, dispatch tool calls, clock, two LLM connections)
- `boros/adapters/__init__.py` — factory: `load_adapter(provider, config) → BaseAdapter`
- `boros/adapters/base_adapter.py` — abstract interface all providers must implement
- `boros/adapters/providers/anthropic.py` — Anthropic API adapter
- `boros/adapters/providers/openai.py` — OpenAI API adapter
- `boros/adapters/providers/ollama.py` — Ollama (local models) adapter
- `boros/adapters/providers/openai_compat.py` — any OpenAI-compatible endpoint adapter
- `boros/manifest.json` — exact content from BOROS.md Section 5
- `boros/config.json` — exact content from BOROS.md Section 6
- `boros/world_model.json` — full 10-category rubrics from BOROS.md Section 7, pre-filled (Eval Generator needs rubrics to score on cycle 1)
- `boros/.env.template` — provider-agnostic, from BOROS.md

**Acceptance:**

```bash
python -c "from boros.adapters import load_adapter; print('OK')"
python -c "import json; m=json.load(open('boros/manifest.json')); assert len(m['boot_sequence'])==10; print('OK')"
python -c "import json; w=json.load(open('boros/world_model.json')); assert len(w['categories'])==10; print('OK')"
```

---

## Phase 2 — Skill Scaffold

**Create all 19 skill directories** with standard layout:

```
boros/skills/{name}/
├── SKILL.md          ← placeholder "# {name}\n\nTo be written."
├── skill.json        ← from manifest entry + Section 9 descriptions
├── functions/
│   └── __init__.py   ← empty
├── state/
├── snapshots/
├── tests/
├── metrics/
│   └── metrics.jsonl ← empty
└── changelog.md      ← "v1.0.0 — MVC seed\n"
```

**Acceptance:**

```bash
python -c "
import os
skills = ['director-interface','mode-controller','temporal-consciousness','identity','memory',
          'skill-router','context-orchestration','reflection','meta-evolution','meta-evaluation',
          'loop-orchestrator','skill-forge','mission','reasoning','attention','tool-use',
          'communication','research','eval-bridge']
for s in skills:
    assert os.path.isdir(f'boros/skills/{s}'), f'Missing {s}'
    assert os.path.isfile(f'boros/skills/{s}/skill.json'), f'Missing {s}/skill.json'
print(f'All {len(skills)} skill directories OK')
"
```

---

## Phase 3 — Critical Seed Skills

**Copy from SEED-SKILLS.md verbatim:**

- Section 1 → `boros/skills/memory/` (all functions, SKILL.md, skill.json)
- Section 2 → `boros/skills/meta-evolution/` (all functions, SKILL.md, skill.json)
- Section 3 → `boros/skills/meta-evaluation/` (all functions, SKILL.md, skill.json, `_internal/prompt_builder.py`)
- Section 4 → `boros/skills/context-orchestration/` (all functions, SKILL.md, skill.json)

**CRITICAL:** Memory functions use `boros/memory/` (top-level), NOT `boros/skills/memory/state/`. All `_get_root()` helpers use `kernel.boros_root` if available, else `Path("boros")`.

**Create top-level memory directory:**

```
boros/memory/
├── evolution_records/
├── sessions/
├── experiences/
├── facts/
├── task_records/
└── score_history.jsonl     ← empty file
```

**Create seed state files for meta-evaluation:**

- `boros/skills/meta-evaluation/state/criteria.json` — from SEED-SKILLS.md Section 3
- `boros/skills/meta-evaluation/state/verdicts.jsonl` — empty
- `boros/skills/meta-evaluation/state/calibration.jsonl` — empty

**Create seed state files for meta-evolution:**

- `boros/skills/meta-evolution/state/proposals/` — empty dir
- `boros/skills/meta-evolution/state/applied.jsonl` — empty
- `boros/skills/meta-evolution/state/rollbacks.jsonl` — empty
- `boros/skills/meta-evolution/state/target_calibration.jsonl` — empty

**Acceptance:**

```bash
python -c "
from boros.skills.memory.functions import memory_stats, memory_read, memory_write
r = memory_stats({})
assert r['status'] == 'ok', r
print('memory_stats OK')
r = memory_read({})
assert r['status'] == 'ok', r
print('memory_read OK')
from boros.skills.meta_evolution.functions import evolve_history
r = evolve_history({})
assert r['status'] == 'ok', r
print('evolve_history OK')
from boros.skills.meta_evaluation.functions import review_history
r = review_history({})
assert r['status'] == 'ok', r
print('review_history OK')
"
```

**Note:** Import paths may need adjustment for hyphens in directory names. Use underscores in Python package names or `importlib`. Handle this in the kernel's skill loader.

---

## Phase 4 — Remaining 15 Skill Implementations

**Generate from SKILLS-REFERENCE.md.** Priority order:

1. Loop Orchestrator (drives everything)
2. Mode Controller (simplest, validates mode works)
3. Skill Router (tool visibility)
4. Reflection (hypothesis writing)
5. Temporal Consciousness
6. Identity
7. Skill Forge (needed for evolution)
8. Eval Bridge (needed for scoring)
9. Mission, Reasoning, Attention, Tool Use, Communication, Research

**For each skill:**

- Implement all functions per the reference spec
- Write SKILL.md following seed skill pattern (purpose, role in loop, functions, rules, seed limitations)
- Write skill.json matching manifest entry
- Create any seed state files listed

**Acceptance:** Every function can be imported and called with empty/minimal params without crashing.

---

## Phase 5 — Director Interface

**Implement skill #0 (NOT LLM-facing):**

- `prompt_toolkit` based terminal UI
- Background thread for evolution loop
- Foreground readline for Director commands
- Command parsing: `boros {command} {args}`
- Dispatch: immediate (`status`) vs queued (everything else → `commands/pending.json`)
- Stream `logs/cycles.log` to terminal
- Ctrl+C: set `pause_requested` flag, loop stops at cycle boundary

**Acceptance:**

```bash
python boros/kernel.py
# Should boot, show 10 skill health checks, accept "boros status"
```

---

## Phase 6 — Eval Generator

**Create `boros/eval-generator/`:**

- `eval_generator.py` — main process
- `config.json` — from BOROS.md Section 14
- `difficulty-config.json` — thresholds
- `categories/` — derived from world_model.json rubrics (Director-visible)
- `shared/requests/` and `shared/results/` — file-based comms
- `generated-tests/` — test prompts (Director can inspect)
- `scoring/` — rubric logic
- `logs/`

**What it does:**

1. Reads category definitions and rubrics
2. Generates randomized test prompts per category at difficulty level
3. Builds a read-only representation of Boros by reading all SKILL.md files + `identity.json` and assembling them into a Claude system prompt — no kernel boot, no tools, no process spawn
4. Sends prompts via Claude API — each test is a separate conversation, no tools, no state change
5. Scores raw text responses against rubrics using GPT-4o
6. Writes result file

**Acceptance:** Eval Generator can receive a request file, generate tests, and write a result file.

---

## Phase 7 — Integration

Wire everything together:

- Loop Orchestrator actually runs cycles (REFLECT → EVOLVE → EVAL)
- Context Orchestration fires at cycle start
- Skill Router swaps tools between stages
- Eval Bridge communicates with Eval Generator
- Snapshot Manager takes snapshots post-eval
- Command queue polling at cycle boundaries
- Git tagging after evals
- Logging to `logs/cycles.log`, `logs/errors.log`, `logs/timing.log`

**Acceptance:** Full cycle runs — boot, REFLECT writes hypothesis, EVOLVE proposes change, Meta-Eval reviews, EVAL scores, records backfilled. Cycle 2 starts with REFLECT reading backfilled records.

---

## Phase 8 — Seed State Initialization

- First-boot detection (check for `session/current_cycle.json`)
- Create all directories on first boot
- Write all seed state files
- Derive `evals/categories.json` from `world_model.json` (names + descriptions only)
- Initialize `skills/eval-bridge/state/high_water_marks.json` — all 10 categories at 0.0
- Initialize `skills/loop-orchestrator/state/loop_state.json` — cycle 0
- Initialize `skills/identity/state/identity.json` — seed content
- Create `commands/pending.json` — `{"pending": []}`
- Create empty dirs: `tasks/queue/`, `tasks/active/`, `tasks/completed/`, `tasks/learning/`
- Create empty dirs: `snapshots/`, `evals/scores/`

**Acceptance:**

```bash
rm -rf boros/session boros/memory  # simulate fresh clone
python boros/kernel.py
# Should detect first boot, create everything, run cycle 1, not crash
```

---

## Done

After Phase 8, Boros is a complete, runnable system. Clone → set API keys → fill world_model.json → `python boros/kernel.py` → evolution begins.
