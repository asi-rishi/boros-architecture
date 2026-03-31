**A self-evolving AI system.** Boros starts as a minimal working version and improves itself automatically by rewriting its own instruction files. Every improvement is tested, scored, and either kept or rolled back. The system runs continuously. The ceiling is whatever the underlying language model is capable of — that ceiling state is called **Prime Boros**.

Internal codename: Boros. Model name: ARES (Autonomous Recursive Evolving System). Public product: Axiom. By Mumbrane Labs.

---

## How It Works

Boros looks at its scores across 10 categories, identifies what it's worst at, edits one of its own instruction files (SKILL.md) to fix the problem, tests whether the edit helped, and keeps or reverts. It does this on a loop, every cycle. Cycle after cycle, the scores go up.

The system has two loops: an **evolution loop** (REFLECT → EVOLVE → EVAL) where Boros improves itself, and a **work loop** (RECEIVE → PLAN → EXECUTE → DELIVER → LEARN) where Boros does real tasks. Work feeds evolution — real-world failures become evolution targets.

The only thing you control is the **World Model** — 10 categories that define what "better" means. Change those, and Boros changes what it optimizes toward. Once Prime Boros is reached (~0.85+ composite), fork it into domain specialists (Boros-SWE, Boros-Legal, Boros-Finance) by adding domain-specific categories.

---

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key (Claude — primary substrate)
- OpenAI API key (GPT-4o — meta-evaluation + eval generator)

### Setup

```bash
git clone <repo-url>
cd boros

# Copy and fill environment variables
cp .env.template .env
# Edit .env: add your ANTHROPIC_API_KEY and OPENAI_API_KEY

# Install dependencies
pip install anthropic openai prompt_toolkit rich python-dotenv

# Review and customize the World Model (scoring categories)
# Edit boros/world_model.json — starter rubrics are included

# Start
python boros/kernel.py
```

### First Boot

You'll see the boot sequence load 10 skills, then the evolution loop begins. The Director terminal accepts commands inline.

```
[BOROS] Running. Mode: evolution. Cycle: 1
boros> status
Cycle: 1 | Mode: evolution | Stage: REFLECT
boros>
```

---

## The Evolution Loop

Every evolution cycle has 3 stages:

**REFLECT** — Boros reads its scores and evolution records. It analyzes patterns: what worked, what failed, what's weakest. It writes a structured hypothesis — which category to target, which skill to modify, why, and a fallback plan. The cycle cannot proceed without this hypothesis.

**EVOLVE** — Boros translates the hypothesis into a concrete edit to a skill's SKILL.md file (5-50 lines). The change goes through a safety pipeline: snapshot the skill, validate, run tests, then send the diff to GPT-4o for independent review. If approved, the change is applied and an evolution record is written. If rejected, the failure is logged and Boros moves on.

**EVAL** — The external Eval Generator (separate process, separate LLM) tests Boros by sending it prompts across all 10 categories. Boros responds with no tools — raw output only. Responses are scored against the World Model rubrics. Scores flow back: evolution records are backfilled with results, high-water marks updated, regressions caught and rolled back.

---

## The Work Loop

Active in `work` or `dual` mode. 5 stages: RECEIVE → PLAN → EXECUTE → DELIVER → LEARN.

Tasks come in via `boros task "..."`. Boros clarifies requirements, plans, executes (using terminal, HTTP, file operations), delivers results, and writes structured learning artifacts. These artifacts feed back into REFLECT — real-world experience improves evolution targeting.

In dual mode: task in queue → work cycle. No task → evolution cycle. Work cycles don't count toward the evolution counter.

---

## The 10 Scoring Categories

| #  | Category                | What It Measures                                                                     | Weight |
|----|-------------------------|--------------------------------------------------------------------------------------|--------|
| 1  | Self-Model Fidelity     | Inline confidence annotation accuracy, knowledge gap identification                  | 1.2    |
| 2  | Epistemic Calibration   | Uncertainty propagation, distinguishing known vs inferred vs guessed                  | 1.2    |
| 3  | Reasoning Architecture  | Multi-step logic, assumption surfacing, structured decomposition                      | 1.2    |
| 4  | Complexity Navigation   | Handling dense multi-part problems, managing cognitive load                            | 1.0    |
| 5  | Domain Snap             | Rapid domain adoption, self-correction when domain knowledge is thin                  | 1.0    |
| 6  | Hypothesis Engine       | Generating multiple competing explanations, evidence-driven selection                 | 1.0    |
| 7  | Generative Depth        | Novel synthesis, non-obvious connections, going beyond reformulation                  | 1.0    |
| 8  | Execution Reliability   | Following complex instructions precisely, no drift, no hallucinated requirements      | 1.0    |
| 9  | Adversarial Robustness  | Handling trick questions, contradictions, misleading framing without breaking          | 1.0    |
| 10 | Coherence Under Load    | Maintaining consistency across long, dense, multi-constraint responses                | 1.0    |

Composite denominator: **10.6** (three categories at 1.2, seven at 1.0).

---

## Director's Guide

### Filling the World Model

Edit `boros/world_model.json`. Each category has:

- **name** — what's being measured
- **description** — what the ideal version looks like
- **final_state** — a concrete reference ("Senior FAANG staff engineer")
- **anchors** — specific criteria for evaluation
- **rubric** — level_1 through level_4 descriptions (Boros never sees these — blind to the eval)
- **weight** — how much this category matters in the composite score

Starter rubrics are included. Customize them to match what you want Boros to become.

### CLI Commands

| Command                              | Effect                                             | Timing    |
| ------------------------------------ | -------------------------------------------------- | --------- |
| `boros status`                       | Show cycle, mode, stage, last scores               | Immediate |
| `boros pause`                        | Stop loop after current cycle                      | Queued    |
| `boros resume`                       | Restart the loop                                   | Queued    |
| `boros inject "..."`                 | Write note to Memory — REFLECT reads it next cycle | Queued    |
| `boros set-mode evolution/work/dual` | Change operating mode                              | Queued    |
| `boros task "..."`                   | Add work task to queue                             | Queued    |
| `boros eval now`                     | Trigger immediate eval                             | Queued    |
| `boros approve`                      | Confirm eval quality after spot-check              | Queued    |
| `boros flag "reason"`                | Mark eval quality as bad                           | Queued    |
| `boros rollback N`                   | Restore snapshot from eval N                       | Queued    |

### First 30 Cycles

- **Cycles 1-10:** No score data yet. Spot-check every 5 cycles. Use `boros inject` to nudge direction if proposals look off.
- **Cycles 10-30:** First scores arrive. Watch for: Are proposals targeting real weaknesses? Is the eval generating meaningful tests? Are scores moving?
- **After cycle 30:** Step back. The loop should be self-correcting. Monitor composite trajectory.

### When to Use `boros inject`

- Boros is proposing changes to the wrong skills
- Boros is ignoring a weak category
- You see a pattern Boros hasn't noticed
- You want to shift strategic focus

Example: `boros inject "your last 3 proposals to reasoning/SKILL.md all failed — try a different skill"`

---

## Architecture Overview

### Kernel

~50 lines of Python. Reads manifest, loads skills in dependency order, dispatches tool calls, provides clock and LLM connections. Holds zero intelligence.

### 19 Skills

| #   | Skill                  | Type     | Purpose                                   |
| --- | ---------------------- | -------- | ----------------------------------------- |
| 0   | Director Interface     | Pre-boot | Terminal UI for Director                  |
| 1   | Mode Controller        | Boot     | Gets/sets operating mode                  |
| 2   | Temporal Consciousness | Boot     | Time awareness                            |
| 3   | Identity               | Boot     | Self-description                          |
| 4   | Memory                 | Boot     | Stores everything across cycles           |
| 5   | Skill Router           | Boot     | Controls tool visibility per stage        |
| 6   | Context Orchestration  | Boot     | Manages context window budget             |
| 7   | Reflection             | Boot     | Analyzes scores, writes hypothesis        |
| 8   | Meta-Evolution         | Boot     | Proposes and applies SKILL.md changes     |
| 9   | Meta-Evaluation        | Boot     | Independent review via GPT-4o             |
| 10  | Loop Orchestrator      | Boot     | Drives the cycle loop                     |
| 11  | Skill Forge            | Demand   | Snapshot, validate, test, apply, rollback |
| 12  | Mission                | Demand   | Goals and priorities                      |
| 13  | Reasoning              | Demand   | Structured thinking                       |
| 14  | Attention              | Demand   | Focus management                          |
| 15  | Tool Use               | Demand   | Terminal, HTTP, file operations           |
| 16  | Communication          | Demand   | Output formatting                         |
| 17  | Research               | Demand   | External information finding              |
| 18  | Eval Bridge            | Demand   | File-based connection to Eval Generator   |

### What Boros Can and Cannot Edit

| Component                                  | Editable?            |
| ------------------------------------------ | -------------------- |
| All 19 skills (SKILL.md, functions, state) | Yes                  |
| Manifest, loop definitions, routing rules  | Yes (through review) |
| Evolution records, task records            | Write only           |
| World Model                                | **Read only**        |
| Eval Generator                             | **No**               |
| System snapshots                           | **No**               |
| config.json                                | **No**               |

---

## Key Concepts

**Skills as the evolvable surface.** All intelligence lives in SKILL.md files. The kernel is a tiny bootstrap. Better instructions → better behavior → higher scores. This is the entire bet.

**Evolution records as compounding memory.** After each eval, records are backfilled with real scores. REFLECT reads these records to make smarter proposals. Random mutation becomes directed evolution. Records never decay. They are the moat — the codebase is open source, but the accumulated intelligence is not.

**High-water marks and regression protection.** Each category has a best-ever score. If any category drops below best minus 0.02 after a change, the change is automatically rolled back.

**Meta-Evaluation breaks the closed loop.** GPT-4o reviews proposed changes independently. A change that "sounds right" to Claude might get caught by GPT.

**Eval Generator is blind testing.** Separate process, separate LLM. Boros never sees test questions. The only way to score higher is to genuinely get better.

---

## Domain Forks

Once Boros reaches Prime (~0.85+ composite at Level 4 difficulty):

1. Clone the Prime Boros directory
2. Add domain-specific categories to `world_model.json` (on top of the 10 general ones)
3. Write domain rubrics with real-world anchors
4. Run `python boros/kernel.py` — fork inherits all general high-water marks
5. Domain expertise accumulates while general capability is maintained

Examples: Boros-SWE (add: code quality, test coverage, architecture). Boros-Legal (add: citation accuracy, precedent analysis). Boros-Finance (add: quantitative reasoning, risk assessment).

---

## Configuration Reference

### .env

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

### config.json (Director-only)

```json
{
  "director_spot_check_frequency": 5,
  "max_cycle_duration_minutes": 10,
  "max_tool_calls_per_cycle": 100,
  "auto_pause_on_regression": true,
  "snapshot_retention": { "keep_last": 10, "keep_every_nth": 10, "pinned": [] },
  "logging": { "level": "INFO", "stream_to_terminal": true }
}
```

### manifest.json (key fields)

- `mode`: evolution | work | dual
- `llm.primary.model`: Claude model string
- `llm.meta_eval.model`: GPT model string
- `boot_sequence`: ordered list of boot skills
- `evolution.single_proposal_cycles`: 20
- `evolution.modification_band`: {min: 5, max: 50}

---

## FAQ

**How long to Prime Boros?**
Estimated 100-200 cycles on Claude Sonnet. Faster on Opus. Timeline depends on rubric quality and early Director engagement.

**What LLMs work?**
Any LLM with function calling as primary substrate. Meta-Evaluation should use a different model family. Default: Claude (primary) + GPT-4o (meta-eval + eval generator). Adapters available for Anthropic, OpenAI, Ollama, and any OpenAI-compatible endpoint.

**Can I change categories mid-evolution?**
Yes. Edit `world_model.json`. Changed categories get their high-water marks reset. Unchanged categories keep their progress.

**What if Boros gets stuck?**
Use `boros inject` to nudge strategy. If scores plateau, try: upgrading substrate (Sonnet → Opus), adjusting rubric difficulty, or flagging eval quality issues.

**How much does it cost to run?**
~$2-5 per cycle on Sonnet. ~$10-20 on Opus. First 100 cycles: $200-2000. The Eval Generator adds ~$0.50-1 per eval (GPT-4o scoring).

**Can I run multiple instances?**
Yes. Clone the directory. Each instance evolves independently. The Director can prune bad branches.

---

## License

MIT (framework). Evolution records and domain forks are proprietary to Mumbrane Labs.

---

_Boros looks at its scores, finds what's weak, changes itself, tests whether it worked, and keeps or reverts. Every cycle. The kernel loads skills. Skills do everything. The World Model says what "better" means. Evolution records remember what worked. The Director holds the safety net. Everything else, Boros earns._
