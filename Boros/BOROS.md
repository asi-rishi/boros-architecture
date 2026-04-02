# BOROS Substrate: Single Source of Truth

**Paradigm:** Unconstrained Autonomy. Boros is an autonomous, self-modifying software engineering substrate. It natively evolves its own architecture, authors its own execution pipelines, and measures its performance against a rigorous, independent external Outcome Validator (Eval Generator). 

This file acts as the ultimate reference doc and System Instruction Set for any LLM driving this substrate.

---

## 1. Directory Structure & Anatomy

The Boros environment is rigidly structured into isolated functional domain boundaries. If you are a freshly connected LLM attempting to interface or evolve the system, strictly adhere to these mappings:

```text
boros/
├── .env.template                # Global API credential configurations
├── config.json                  # Engine timers, logging, and fallback adapter overrides
├── manifest.json                # Master skill definitions, boot orders, and payload signatures
├── kernel.py                    # The mechanical beating heart. Auto-loads adapters and tool functions
├── adapters/                    # Provider connections (Anthropic, OpenAI, etc.) via base_adapter 
├── commands/                    # Interactive Director UI queue -> `pending.json`
├── evals/                       # World Model scoring thresholds and categories
├── logs/                        # `cycles.log`, `errors.log`, etc.
├── memory/                      # **The Moat**. Contains Long-Term memory structures:
│   ├── evolution_records/       # Historical patches, diffs, and verdicts
│   ├── experiences/             # Qualitative lessons and narrative facts
│   ├── sessions/                # Short-term rolling buffer states
│   └── score_history.jsonl      # Chronological ledger of dual-scoring evaluations
├── session/                     # Volatile cycle state (`loop_state.json`, `current_cycle.json`)
├── skills/                      # The 19 Autonomous Brain lobes
│   └── [skill-name]/            # e.g., `tool-use`, `memory`, `meta-evolution`
│       ├── SKILL.md             # The semantic intent and prompt instruction of the capability
│       ├── skill.json           # Physical skill metadata
│       └── functions/           # The ACTUAL python algorithms (evolved by Boros)
└── eval-generator/              # An independent sandbox environment to test Boros's capabilities
```

---

## 2. The 3-Stage Evolution Loop

Boros fundamentally compounds intelligence via a 3-stage infinite recursive loop. The `kernel.py` loads the components, but the `Loop Orchestrator` spins the timing.

1. **REFLECT**: Boros reads the `context_manifest.json` (prepared dynamically by `Context Orchestration` at cycle boot). It evaluates previous historical evaluation scores, parses weakest execution categories, and natively writes a mathematical and qualitative `hypothesis.json`.
2. **EVOLVE**: Boros takes its hypothesis, isolates a functional bottleneck mapped in `manifest.json`, and deliberately writes structural Python code inside a specific `boros/skills/**/functions/` directory or modifies a `SKILL.md` instruction block. Boros then submits this diff to the `Meta-Evaluation` Review Board (a secondary LLM pipeline), which strictly grades the execution for regressions. If it passes, it's structurally committed.
3. **EVAL**: The `Eval Bridge` initiates contact with the isolated `boros/eval-generator/` Sandbox. The Generator spawns complex tasks, permits Boros 20 Tool Invocation rounds within the sandbox to solve the problem, scores Boros based on literal success matrices (60% Outcome Validation / 40% LLM Quality Reasoning), and returns a Composite score back to Boros memory to conclude the cycle.

---

## 3. Tool Utilization & Unconstrained Execution

You are granted unbounded file system capability. Do not artificially throttle operations.

Boros natively interfaces with the Substrate through **Skill #14 — Tool Use**, which supplies:
- `tool_terminal(command, background)`: For running native Powershell/Bash environments. Returns `stdout`. Captures asynchronous `job_id` keys for background daemon spins.
- `tool_file_edit_diff(target_file, replacement_chunks)`: Surgical multi-instance diff-block replacement, rendering monolithic file-rewriting obsolete.

All Python scripts are auto-resolved relative to the project container, meaning `import boros` naturally queries upwards without configuration limits.

---

## 4. Adapters & LLM Connectivity

The physical "Brain" of Boros communicates through `adapters/base_adapter.py`. 
Any API LLM (Claude, GPT, Ollama) hooks directly into the factory function located in `kernel.py`:
```python
self.evolution_llm = load_adapter(self.config["providers"]["evolution_api"])
self.meta_eval_llm = load_adapter(self.config["providers"]["meta_eval_api"])
```

**If you are a fresh Agent tasked with bringing Boros online:**
1. Populate actual payload serializations inside `adapters/providers/anthropic.py` (or `openai.py`) tracking `params` arrays and mapping to `.env` keys.
2. Intercept the placeholder logic in `boros/skills/director-interface/functions/interface.py` to strip the temporary `time.sleep(2)` scaffold and seamlessly query `evolution_llm` sequentially.

---

## 5. Core Skill Reference Matrix

There are 19 unique Capabilities separated natively into *Boot* sequences (load sequentially verifying constraints) and *Demand* load structures (dynamically invoked as necessary to offset token burn).

| Classification | Essential Skills | Description |
| :--- | :--- | :--- |
| **Director** | `director-interface` | The asynchronous `prompt_toolkit` Terminal UI wrapper. |
| **Boot Core** | `identity`, `memory`, `skill-router`, `reflection` | Establishes the static personality, physical database connections, mapping tools, and cycle starting analysis blocks. |
| **Boot Evolution** | `meta-evolution`, `meta-evaluation`, `loop-orchestrator` | Proposes raw codebase changes, rigorously audits diff regressions, and manages the state definitions (`session/`). |
| **Demand** | `tool-use`, `skill-forge`, `web-research`, `eval-bridge` | Physical filesystem manipulation, automated PyTest safety compiling, headless browser integrations, and the bridge to the dual-scoring Eval Sandbox. |

---

## 6. How to Extend This Source of Truth

**Boros is designed to self-mutate.**
As you natively rewrite the Python functionality of `boros/skills/*/functions`, you must independently maintain alignment with this `BOROS.md` truth block. Evolve the system safely.
