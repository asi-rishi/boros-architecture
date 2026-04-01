BOROS — Complete Technical Specification

> **Single source of truth.** Read fully before building. Do not infer, assume, or improvise — everything needed is here.

> **Name:** Boros (system, product, company identifier — all usage). **Company:** Mumbrane Labs. In all code, comments, and file references, use `boros` as the identifier.

---

## Table of Contents

1. [What Boros Is](#1-what-boros-is)
2. [Core Objective](#2-core-objective)
3. [Folder Structure](#3-folder-structure)
4. [The Kernel](#4-the-kernel)
4b. [Adapters — Provider-Agnostic LLM Interface](#4b-adapters--provider-agnostic-llm-interface)
5. [Manifest Schema](#5-manifest-schema)
6. [Config Schema](#6-config-schema)
7. [World Model Schema](#7-world-model-schema)
8. [Skill Standard](#8-skill-standard)
9. [All 19 Skills](#9-all-19-skills)
10. [Boot Sequence](#10-boot-sequence)
11. [Evolution Loop](#11-evolution-loop)
12. [Evolution Mechanics](#12-evolution-mechanics)
13. [Meta-Evaluation Protocol](#13-meta-evaluation-protocol)
14. [Eval Generator](#14-eval-generator)
15. [Snapshot Manager](#15-snapshot-manager)
16. [Memory](#16-memory)
17. [Context Orchestration](#17-context-orchestration)
18. [Work Loop](#18-work-loop)
19. [Director Interface](#19-director-interface)
20. [Director CLI Reference](#20-director-cli-reference)
21. [Session vs Memory Lifecycle](#21-session-vs-memory-lifecycle)
22. [Runtime Model](#22-runtime-model)
23. [The 10 Scoring Categories](#23-the-10-scoring-categories)
24. [Access Control](#24-access-control)
25. [Build Order](#25-build-order)
26. [Seed Skill Index](#26-seed-skill-index)
27. [Complete File Structure](#27-complete-file-structure)

---

## 1. What Boros Is

Boros is a self-improving AI system. It starts as a minimal working version and improves itself automatically by rewriting its own instruction files (SKILL.md) and authoring executable Python code. Every improvement is tested, scored, and either kept or rolled back. The system runs continuously. All intelligence lives in skills — structured directories containing an instruction file, function implementations, and state. The kernel is a tiny bootstrap that loads skills and routes messages. Everything else — including the evolution harness itself — is a skill and therefore evolvable.

> **Design philosophy (Unconstrained Autonomy):** Boros is not constrained by hardcoded guardrails, tool limits, or API restrictions. It is a seed built to grow whatever limbs it requires. The Skill Router exposes the full tool manifest globally at all times — Boros's own intelligence decides which tools to use when. The World Model provides evolution pressure; safety comes from Meta-Evaluation review (GPT-4o code review board), not from hiding tools.

---

## 2. Core Objective

Boros looks at its scores across 10 categories, identifies what it is worst at, edits one of its own instruction files to fix the problem, tests whether the edit helped, and keeps or reverts. It does this on a loop, every cycle. Cycle after cycle, the scores go up. The ceiling is whatever the underlying language model is capable of — that ceiling state is called **Prime Boros**.

Once Prime Boros is reached, the system can be forked into specialized versions by adding domain-specific scoring pressure (Boros-SWE, Boros-Legal, Boros-Finance, Boros-Ops). All of that comes from changing what is being scored — not from rewriting the system.

The Director's only real control surface is the **World Model** — the 10 categories and their scoring criteria. Change those, and Boros changes what it optimizes toward.

---

## 3. Folder Structure

Everything lives in one folder. Clone it, set API keys, fill `world_model.json`, run `python kernel.py`. Everything accumulates inside it.

```
boros/
├── kernel.py
├── manifest.json
├── config.json
├── world_model.json
│
├── adapters/
│   ├── __init__.py          ← factory: load_adapter(provider, config) → BaseAdapter
│   ├── base_adapter.py      ← abstract interface all providers must implement
│   └── providers/
│       ├── anthropic.py     ← Anthropic API
│       ├── openai.py        ← OpenAI API
│       ├── ollama.py        ← Ollama (local models)
│       ├── openai_compat.py ← any OpenAI-compatible endpoint (Together, Groq, Mistral, etc.)
│       └── gemini.py        ← Google Gemini API
│
├── skills/
│   ├── director-interface/
│   ├── mode-controller/
│   ├── temporal-consciousness/
│   ├── identity/
│   ├── memory/
│   ├── skill-router/
│   ├── context-orchestration/
│   ├── reflection/
│   ├── meta-evolution/
│   ├── meta-evaluation/
│   ├── loop-orchestrator/
│   ├── skill-forge/
│   ├── mission-control/
│   ├── reasoning/
│   ├── scratchpad/
│   ├── tool-use/
│   ├── communication/
│   ├── web-research/
│   └── eval-bridge/
│
├── session/
│   ├── current_cycle.json
│   ├── hypothesis.json
│   ├── context_manifest.json
│   ├── context_report.json
│   └── scratchpad.json
│
├── memory/
│   ├── evolution_records/
│   ├── sessions/
│   ├── experiences/
│   ├── facts/
│   ├── task_records/
│   └── score_history.jsonl
│
├── evals/
│   ├── categories.json
│   └── scores/
│
├── snapshots/
│   ├── snapshot-index.json
│   └── eval-{id}/
│
├── eval-generator/
│   ├── eval_generator.py
│   ├── config.json
│   ├── difficulty-config.json
│   ├── categories/
│   ├── shared/
│   │   ├── .ready
│   │   ├── requests/
│   │   └── results/
│   ├── generated-tests/
│   ├── scoring/
│   └── logs/
│
├── commands/
│   └── pending.json
│
├── tasks/
│   ├── queue/
│   ├── active/
│   ├── completed/
│   └── learning/
│
└── logs/
    ├── cycles.log
    ├── errors.log
    └── timing.log
```

Each skill directory follows the same layout:

```
skill-name/
├── SKILL.md
├── skill.json
├── functions/
│   ├── __init__.py
│   └── {function}.py
├── state/
├── snapshots/
├── tests/
│   └── test_{skill}.py
├── metrics/
│   └── metrics.jsonl
└── changelog.md
```

---

## 4. The Kernel

**File:** `boros/kernel.py`
**Size:** ~50 lines
**Language:** Python

### Responsibilities

1. Spawn the Eval Generator subprocess before boot
2. Read `manifest.json`
3. Load skills in dependency order (topological sort — hard fail on circular dependencies)
4. Dispatch language model tool calls via flat function registry (`name → callable`)
5. Provide a raw UTC clock
6. Own the two language model connections (primary + meta-eval)

### What the kernel does NOT do

- Run loops (Loop Orchestrator)
- Manage modes (Mode Controller)
- Call evals (Eval Bridge)
- Decide what the LLM sees (Skill Router + Context Orchestration)
- Hold any intelligence

### Kernel attributes

| Attribute | Type | Purpose |
|-----------|------|---------|
| `kernel.registry` | dict | function_name → callable |
| `kernel.primary_llm` | BaseAdapter instance | Primary substrate — provider set in manifest |
| `kernel.meta_eval_llm` | BaseAdapter instance | Meta-evaluation — provider set in manifest |
| `kernel.clock` | callable | Returns UTC timestamp |
| `kernel.manifest` | dict | Loaded manifest |
| `kernel.config` | dict | Loaded config |
| `kernel.boros_root` | Path | Path to `boros/` folder |

### Eval Generator subprocess

Before loading any skill, the kernel spawns `eval-generator/eval_generator.py` as a child subprocess. The kernel then polls for the sentinel file `eval-generator/shared/.ready`, which the Eval Generator writes as its last step before entering its request-polling loop. Polling timeout is 30 seconds. If the sentinel does not appear within that window, the kernel halts with a clear error message and exits. The Eval Generator process is a child of the kernel process — when the kernel is killed, the child terminates with it. No orphan processes.

### Boot behavior

**First-ever boot:** Detected by the absence of `session/current_cycle.json`. All directories are created, seed state files are written, and `evals/categories.json` is derived from `world_model.json`.

**Restart:** Start a fresh cycle. No mid-cycle resume. Interrupted cycles are abandoned.

### Skill loading

For each skill in the boot sequence: read `skill.json`, import `functions/__init__.py`, register each function in `kernel.registry`, run `health_check()` if defined. Any `health_check` failure halts the boot entirely.

Demand skills are not loaded at boot — they load on first use.

### Message loop

The kernel owns the mechanical send/receive/dispatch loop. This is dumb plumbing — no intelligence. It sends a message batch to the primary LLM, receives a response, dispatches any tool-use blocks to the registered function, appends results back to the message history, and loops. The LLM decides when to advance stages and end cycles by calling Loop Orchestrator tools. When `loop_end_cycle` is called, the kernel discards conversation history and starts a fresh conversation for the next cycle.

### Function dispatch

When the LLM returns a tool-use block, the kernel looks up the function name in `kernel.registry`, calls `function(params, kernel)`, and returns the result to the LLM as a tool result. Every function takes `params: dict` and an optional `kernel` reference.

---

## 4b. Adapters — Provider-Agnostic LLM Interface

All LLM calls go through the adapter layer. The kernel never calls an LLM API directly. Any role (primary substrate, meta-evaluation, eval generator) can use any provider.

### BaseAdapter interface

Every adapter must implement this interface:

```python
class BaseAdapter:
    def complete(self, messages: list, tools: list = None, system: str = None) -> dict:
        """Send messages, return structured response with content blocks."""
        raise NotImplementedError

    def stream(self, messages: list, tools: list = None, system: str = None):
        """Optional streaming. Raise NotImplementedError to disable."""
        raise NotImplementedError

    @property
    def supports_tools(self) -> bool:
        """Return False for providers that don't support function calling."""
        return True
```

`complete()` always returns a normalized dict:
```json
{
  "content": [
    {"type": "text", "text": "..."},
    {"type": "tool_use", "name": "function_name", "id": "...", "input": {...}}
  ],
  "stop_reason": "tool_use | end_turn | max_tokens",
  "usage": {"input_tokens": 0, "output_tokens": 0}
}
```

### Factory

`adapters/__init__.py` exports `load_adapter(role_config: dict) → BaseAdapter`. It reads the `provider` key from the manifest role config and loads the corresponding class from `adapters/providers/{provider}.py`. Unknown providers raise a clear error at boot, not at runtime.

### Built-in providers

| Provider key | File | Notes |
|---|---|---|
| `anthropic` | `providers/anthropic.py` | Anthropic API. Requires `ANTHROPIC_API_KEY`. |
| `openai` | `providers/openai.py` | OpenAI API. Requires `OPENAI_API_KEY`. |
| `ollama` | `providers/ollama.py` | Local Ollama server. No API key. `base_url` defaults to `http://localhost:11434`. Tool support depends on model. |
| `openai_compat` | `providers/openai_compat.py` | Any OpenAI-compatible endpoint (Together, Groq, Mistral, Anyscale, etc.). Requires `base_url` and `api_key_env` (name of the env var holding the key). |
| `gemini` | `providers/gemini.py` | Google Gemini API. Requires `GEMINI_API_KEY`. |

### Adding a new provider

Drop a file at `adapters/providers/{name}.py` that subclasses `BaseAdapter`. Set `"provider": "{name}"` in the manifest. The factory loads it automatically — no kernel changes required.

### Provider constraints

If `supports_tools` returns `False` (e.g., a model that doesn't support function calling), the kernel falls back to XML-tag parsing for tool dispatch. This fallback is implemented in the kernel's dispatch loop, not in the adapter.

---

## 5. Manifest Schema

**File:** `boros/manifest.json`
Editable by Boros (changes go through Meta-Evaluation review).

```json
{
  "version": "1.0.0",
  "mode": "evolution",
  "llm": {
    "primary": [
      {
        "provider": "anthropic",
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 8192,
        "temperature": 1.0
      },
      {
        "provider": "gemini",
        "model": "gemini-1.5-pro",
        "temperature": 1.0
      },
      {
        "provider": "openai",
        "model": "gpt-4o",
        "temperature": 1.0
      },
      {
        "provider": "ollama",
        "model": "llama3",
        "base_url": "http://localhost:11434"
      },
      {
        "provider": "openai_compat",
        "model": "mistral-7b",
        "base_url": "https://api.together.xyz/v1",
        "api_key_env": "TOGETHER_API_KEY"
      }
    ],
    "meta_eval": [
      {
        "provider": "openai",
        "model": "gpt-4o"
      },
      {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022"
      },
      {
        "provider": "gemini",
        "model": "gemini-1.5-pro"
      }
    ],
    "eval_generator": [
      {
        "provider": "openai",
        "model": "gpt-4o"
      },
      {
        "provider": "anthropic",
        "model": "claude-3-5-sonnet-20241022"
      }
    ]
  },
  "boot_sequence": [
    "mode-controller",
    "temporal-consciousness",
    "identity",
    "memory",
    "skill-router",
    "context-orchestration",
    "reflection",
    "meta-evolution",
    "meta-evaluation",
    "loop-orchestrator"
  ],
  "skills": {
    "mode-controller": {
      "path": "skills/mode-controller",
      "type": "boot",
      "dependencies": [],
      "provided_functions": ["mode_get", "mode_set"]
    },
    "temporal-consciousness": {
      "path": "skills/temporal-consciousness",
      "type": "boot",
      "dependencies": ["mode-controller"],
      "provided_functions": [
        "time_now",
        "time_elapsed_since",
        "time_cycle_started",
        "time_estimate_remaining"
      ]
    },
    "identity": {
      "path": "skills/identity",
      "type": "boot",
      "dependencies": ["mode-controller"],
      "provided_functions": ["identity_read", "identity_update"]
    },
    "memory": {
      "path": "skills/memory",
      "type": "boot",
      "dependencies": ["mode-controller", "identity"],
      "provided_functions": [
        "memory_page_in",
        "memory_page_out",
        "memory_search_sql",
        "memory_commit_archival"
      ]
    },
    "skill-router": {
      "path": "skills/skill-router",
      "type": "boot",
      "dependencies": ["mode-controller"],
      "provided_functions": [
        "router_get_tools",
        "router_get_budget",
        "router_manifest"
      ]
    },
    "context-orchestration": {
      "path": "skills/context-orchestration",
      "type": "boot",
      "dependencies": ["mode-controller", "identity", "memory"],
      "provided_functions": ["context_load", "context_get_manifest"]
    },
    "reflection": {
      "path": "skills/reflection",
      "type": "boot",
      "dependencies": ["mode-controller", "memory"],
      "provided_functions": [
        "reflection_analyze_trace",
        "reflection_write_hypothesis",
        "reflection_read_hypothesis"
      ]
    },
    "meta-evolution": {
      "path": "skills/meta-evolution",
      "type": "boot",
      "dependencies": ["mode-controller", "memory", "reflection"],
      "provided_functions": [
        "evolve_orient",
        "evolve_set_target",
        "evolve_propose",
        "evolve_apply",
        "evolve_rollback",
        "evolve_create_skill",
        "evolve_modify_loop",
        "evolve_history"
      ]
    },
    "meta-evaluation": {
      "path": "skills/meta-evaluation",
      "type": "boot",
      "dependencies": ["mode-controller", "memory"],
      "provided_functions": [
        "review_proposal",
        "review_modify",
        "review_criteria_update",
        "review_history"
      ]
    },
    "loop-orchestrator": {
      "path": "skills/loop-orchestrator",
      "type": "boot",
      "dependencies": ["mode-controller"],
      "provided_functions": [
        "loop_start",
        "loop_advance_stage",
        "loop_end_cycle",
        "loop_get_state"
      ]
    },
    "skill-forge": {
      "path": "skills/skill-forge",
      "type": "demand",
      "dependencies": [],
      "provided_functions": [
        "forge_invoke",
        "forge_test_suite",
        "forge_snapshot",
        "forge_validate",
        "forge_apply_diff",
        "forge_rollback",
        "forge_create_skill"
      ]
    },
    "mission-control": {
      "path": "skills/mission-control",
      "type": "demand",
      "dependencies": [],
      "provided_functions": ["mission_read", "mission_queue_task", "mission_update_status"]
    },
    "reasoning": {
      "path": "skills/reasoning",
      "type": "demand",
      "dependencies": [],
      "provided_functions": [
        "reason_decompose",
        "reason_evaluate_options",
        "reason_check_logic"
      ]
    },
    "scratchpad": {
      "path": "skills/scratchpad",
      "type": "demand",
      "dependencies": [],
      "provided_functions": ["scratchpad_write", "scratchpad_read", "scratchpad_clear"]
    },
    "tool-use": {
      "path": "skills/tool-use",
      "type": "demand",
      "dependencies": [],
      "provided_functions": [
        "tool_terminal",
        "tool_terminal_input",
        "tool_terminal_kill",
        "tool_file_edit_diff"
      ]
    },
    "communication": {
      "path": "skills/communication",
      "type": "demand",
      "dependencies": [],
      "provided_functions": ["comm_broadcast", "comm_listen"]
    },
    "web-research": {
      "path": "skills/web-research",
      "type": "demand",
      "dependencies": [],
      "provided_functions": [
        "research_browse",
        "research_search_engine",
        "research_archive_source"
      ]
    },
    "eval-bridge": {
      "path": "skills/eval-bridge",
      "type": "demand",
      "dependencies": [],
      "provided_functions": [
        "eval_request",
        "eval_read_scores",
        "eval_backfill",
        "eval_check_regression",
        "eval_update_high_water"
      ]
    }
  },
  "tool_routing": "unconstrained",
  "_tool_routing_note": "All tools are globally available at all times. Boros's intelligence decides which tools to use. The Skill Router injects the entire tool manifest for every API call. Stage transitions update system prompt context but do not hide/show tools.",
  "evolution": {
    "single_proposal_cycles": 20,
    "max_proposals_per_cycle": 5,
    "modification_band": { "min_lines": 5, "max_lines": 50 },
    "eval_frequency": 1
  },
  "context": {
    "max_context_tokens": 200000,
    "memory_token_cap": 8000
  }
}
```

**Model configuration:** Ships with `claude-haiku-4-5-20251001` as the default primary substrate for bootstrap cycles (1–30). Director upgrades by editing `manifest.json` → `llm.primary.model`. Recommended progression:

| Phase | Cycles | Model |
|-------|--------|-------|
| Bootstrap | 1–30 | `claude-haiku-4-5-20251001` |
| Signal | 30–60 | `claude-sonnet-4-6` |
| Acceleration | 60–100 | `claude-sonnet-4-6` |
| Prime | 100+ | `claude-opus-4-6` |

---

## 6. Config Schema

**File:** `boros/config.json`
Director-only. Boros cannot read or modify this file.

```json
{
  "director_spot_check_frequency": 5,
  "spot_check_timeout_minutes": 0,
  "max_cycle_duration_minutes": 10,
  "max_tool_calls_per_cycle": 100,
  "auto_pause_on_regression": true,
  "snapshot_retention": {
    "keep_last": 10,
    "keep_every_nth": 10,
    "pinned": []
  },
  "logging": {
    "level": "INFO",
    "stream_to_terminal": true
  }
}
```

**`spot_check_timeout_minutes`:** When set to `0` (default), spot-check blocks until the Director responds with `boros approve` or `boros flag`. When set to a non-zero value, the loop auto-approves after that many minutes and writes a fact to memory noting the auto-approval. Never set to non-zero in production without intentional unattended operation.

### Environment Variables

**File:** `boros/.env`

```
# Required for default config (Anthropic primary + OpenAI meta-eval)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Add keys for any additional providers used in manifest.json
# GEMINI_API_KEY=
# TOGETHER_API_KEY=
# GROQ_API_KEY=
# MISTRAL_API_KEY=
```

Read at boot via `dotenv`. The kernel loads only the keys required by the providers named in `manifest.json`. If a provider is configured but its key is missing, the kernel halts at boot with a clear error. Ollama and other local providers require no API key.

---

## 7. World Model Schema

**File:** `boros/world_model.json`

The Director edits this file directly. Boros reads it at the start of each cycle via `evals/categories.json` — a derived view containing names, descriptions, final states, and anchors only. Boros never sees rubrics, weights, or test questions.

Each category entry:

```json
{
  "name": "string",
  "description": "string",
  "final_state": "string — the ideal level, described as a role or reference",
  "anchors": ["list of evaluation dimensions"],
  "rubric": {
    "level_1": "string",
    "level_2": "string",
    "level_3": "string",
    "level_4": "string"
  },
  "weight": 1.0
}
```

Ships pre-filled with all 10 categories and rubrics. The Eval Generator needs rubrics to score on cycle 1 — empty rubrics cause EVAL to fail immediately.

**Changing a category definition resets its high-water mark.**

---

## 8. Skill Standard

Every skill follows the same contracts.

### skill.json schema

```json
{
  "name": "skill-name",
  "type": "boot | demand",
  "description": "one-line purpose",
  "dependencies": ["list of skill names"],
  "provided_functions": ["list of function names"],
  "stage_visibility": ["REFLECT", "EVOLVE", "EVAL"],
  "version": "1.0.0",
  "health_check": "function_name | null"
}
```

### SKILL.md contract

Written in plain language. Tells the language model what this skill is for, when to use each function, what each function expects and returns, how this skill relates to other skills, rules and constraints, and current seed limitations.

**SKILL.md is the file that evolution modifies.** Better instructions → better behavior → higher scores.

### Function signature contract

Every function signature: `function_name(params: dict, kernel=None) → dict`

- `params`: all input as a flat dict
- `kernel`: reference to the kernel instance (for registry, LLM connections, clock, paths)
- Returns: always a dict with at minimum `{"status": "ok" | "error"}`
- On error: `{"status": "error", "error": "description"}`
- Never raises uncaught exceptions

### health_check contract

Called at boot during skill loading. Must return without error if the skill is operational. Validates that state files exist and are readable. If it returns `{"status": "error"}` or raises an exception, boot halts.

---

## 9. All 19 Skills

---

### Skill #0 — Director Interface (Pre-boot)

**Type:** Pre-boot — not part of the 10-skill health-check sequence
**Dependencies:** None
**Purpose:** Interactive terminal UI. Wraps the kernel in a background thread. Director types commands inline.

**Implementation:** Built with `prompt_toolkit` and `rich`. The evolution loop runs in a background thread; Director input runs in the foreground. Ctrl+C sets a `pause_requested` flag — the loop stops at the next cycle boundary.

This skill is NOT LLM-facing. No SKILL.md is needed. It is pure terminal infrastructure.

**Responsibilities:**
- Spawn the kernel in a background thread
- Stream `logs/cycles.log` to terminal in real time
- Accept and parse Director commands
- Execute `status` immediately; write all other commands to `commands/pending.json`
- Handle Ctrl+C gracefully

---

### Skill #1 — Mode Controller (Boot)

**Type:** Boot
**Dependencies:** None
**Purpose:** Tracks and sets the operating mode: `evolution`, `work`, or `dual`.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `mode_get` | `() → {status, mode}` | Returns current mode from manifest |
| `mode_set` | `({mode}) → {status, mode}` | Validates and writes new mode to manifest |

**health_check:** `mode_get`
**State files:** None (reads/writes `manifest.json`)

---

### Skill #2 — Temporal Consciousness (Boot)

**Type:** Boot
**Dependencies:** Mode Controller
**Purpose:** Gives Boros a sense of time. Tracks elapsed time, cycle durations, budget consumption.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `time_now` | `() → {status, timestamp}` | Current UTC timestamp via kernel clock |
| `time_elapsed_since` | `({timestamp}) → {status, elapsed_seconds, elapsed_human}` | Duration since a given ISO timestamp |
| `time_cycle_started` | `() → {status, started_at}` | When the current cycle began |
| `time_estimate_remaining` | `({budget_minutes}) → {status, remaining_seconds, pct_used}` | Estimated time left in cycle |

**health_check:** `time_now`
**State files:** `state/cycle_times.jsonl` — append-only log of cycle durations

---

### Skill #3 — Identity (Boot)

**Type:** Boot
**Dependencies:** Mode Controller
**Purpose:** Holds Boros's name, purpose statement, and self-description. Starts minimal and evolves.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `identity_read` | `() → {status, identity}` | Returns current identity object |
| `identity_update` | `({field, value}) → {status}` | Updates a specific field |

**health_check:** `identity_read`
**State files:** `state/identity.json`

Seed content:

```json
{
  "name": "Boros",
  "purpose": "Self-improving AI system. I look at my scores, find what I'm worst at, change my own instructions to fix it, test whether it worked, and keep or revert. Every cycle.",
  "model_name": "ARES",
  "substrate": "claude-haiku-4-5-20251001",
  "created": "",
  "capabilities": {},
  "values": {},
  "self_narrative": ""
}
```

---

### Skill #4 — Memory (Boot)

**Type:** Boot
**Dependencies:** Mode Controller, Identity
**Purpose:** SOTA autonomous tiered memory system (MemGPT-style). Splits data into Working Memory (active prompt state), Recall Memory (local SQLite for metadata/SQL queries), and Archival/Vector Memory (local serverless semantic indexing). Boros actively pages context in and out.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `memory_page_in` | `({query, store?, limit?}) → {status, records, tokens}` | Retrieves records from Recall or Archival memory and loads them into working memory |
| `memory_page_out` | `({record_ids}) → {status}` | Evicts specified records from working memory back to persistent storage |
| `memory_search_sql` | `({sql_query}) → {status, results}` | Direct SQL query against the Recall Memory SQLite database for structured metadata retrieval |
| `memory_commit_archival` | `({content, tags?, metadata?}) → {status, record_id}` | Writes new content to the Archival/Vector store with optional semantic tags |

**health_check:** `memory_search_sql` with a simple `SELECT 1` validation

**Memory stores** — all under `boros/memory/`, NOT under `boros/skills/memory/state/`:

| Store | Location | Contents |
|-------|----------|----------|
| Evolution records | `memory/evolution_records/` | One JSON file per proposed change |
| Sessions | `memory/sessions/` | One JSON file per completed cycle |
| Experiences | `memory/experiences/` | Structured lessons learned |
| Facts | `memory/facts/` | Things Boros discovers about itself |
| Task records | `memory/task_records/` | Completed work tasks |
| Score history | `memory/score_history.jsonl` | Every eval result, append-only |

**Record ID format:** `{prefix}-{cycle:04d}-{n:03d}`
Prefixes: `rec` (evolution_record), `ses` (session), `exp` (experience), `fct` (fact), `tsk` (task_record)

**Tiered architecture:**
- **Working Memory:** Active content injected into the LLM prompt. Managed by Context Orchestration.
- **Recall Memory:** Local SQLite database for structured queries against metadata (record IDs, timestamps, categories, scores, tags). Fast indexed access.
- **Archival Memory:** Serverless vector database (LanceDB/ChromaDB) for semantic similarity search. Stores full record content for retrieval by meaning.

Boros uses `memory_page_in` and `memory_page_out` to actively manage what sits in its working context, bypassing static token caps. This is the foundation for intelligent context management.

**SKILL.md:** Provided as seed file (see Section 26).

---

### Skill #5 — Skill Router (Boot)

**Type:** Boot
**Dependencies:** Mode Controller
**Purpose:** Exposes the full tool manifest globally at all times. All tools are available concurrently for every API call — Boros’s own intelligence decides which to use. Stage transitions update the system prompt context but do not hide or show tools.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `router_get_tools` | `() → {status, tools}` | Returns the complete set of Anthropic-format tool definitions. No stage filtering — all tools always. |
| `router_get_budget` | `() → {status, tool_tokens, remaining_tokens}` | Token cost of the full tool manifest |
| `router_manifest` | `() → {status, manifest}` | Returns the full skill/function manifest for introspection |

**health_check:** `router_get_tools`
**State files:** `state/routing_rules.json` — Boros-evolvable overrides. Seed: empty `{}`

> **Architecture note:** The original design used per-stage `stage_visibility` arrays to control tool access. This was retired in favor of unconstrained global tool access per the Unconstrained Autonomy refactoring. The `tool_routing: "unconstrained"` flag in `manifest.json` governs this behavior.

---

### Skill #6 — Context Orchestration (Boot)

**Type:** Boot
**Dependencies:** Mode Controller, Identity, Memory
**Purpose:** Lean, OS-style context loader with Associative Whispers. Injects only the Working Memory Core (~1,000–2,000 tokens: Identity, Mode, high-level scores, recent commands) plus the top 1–3 most relevant past summaries (~300 tokens of “Whispers” from semantic vector search). Leaves the remainder of the context window empty for Boros to autonomously page in deeper context via Memory tools.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `context_load` | `({focus?}) → {status, loaded, manifest, content}` | Fires at cycle start. Builds context window. Returns metadata AND the actual serialized memory text. |
| `context_get_manifest` | `() → {status, manifest}` | Returns the ~200-token summary of what is and isn't loaded |

**`context_load` return schema:**

```json
{
  "status": "ok",
  "loaded": {
    "identity": { "tokens": 200, "items": 1 },
    "scores": { "tokens": 400, "items": 1 },
    "evolution_records": { "tokens": 4000, "items": 15 },
    "experiences": { "tokens": 1200, "items": 8 },
    "task_context": { "tokens": 0, "items": 0 }
  },
  "manifest": { "...": "~200 token summary" },
  "content": "=== IDENTITY ===\n...\n=== SCORE HISTORY ===\n...\n=== EVOLUTION RECORDS ===\n...\n=== EXPERIENCES ===\n..."
}
```

The `content` field is the actual serialized text of all loaded records, formatted as labeled sections. This is injected directly as block 4 of the system prompt by Loop Orchestrator. Without it, REFLECT is blind — the manifest says records are loaded but none are readable. The existing token-counting loop already reads each file; `content` stores the text alongside the count rather than discarding it.

**Budget profiles:**

Evolution mode:

| Category | Soft Cap % |
|----------|-----------|
| Identity | 5% |
| Temporal | 2% |
| Scores | 10% |
| Evolution records | 50% |
| Experiences | 15% |
| Task context | 15% |
| Overflow buffer | 3% |

Work mode:

| Category | Soft Cap % |
|----------|-----------|
| Identity | 3% |
| Temporal | 2% |
| Scores | 3% |
| Evolution records | 10% |
| Experiences | 10% |
| Task context | 65% |
| Overflow buffer | 7% |

**Budget rules:**
- Percentages are soft caps per category, not fill targets
- Unused allocation pools into the overflow buffer
- Overflow is available to any category that needs more
- `focus` param is ignored at seed — stable interface for future evolution

**Context manifest format** (`session/context_manifest.json`):

```json
{
  "cycle": 42,
  "mode": "evolution",
  "total_budget_tokens": 180000,
  "tool_tokens": 20000,
  "content_tokens_used": 6500,
  "loaded": {
    "identity": { "tokens": 200, "items": 1 },
    "scores": { "tokens": 400, "items": 1, "source": "score_history.jsonl" },
    "evolution_records": { "tokens": 4000, "items": 15, "newest": "rec-0041-001", "oldest": "rec-0028-001" },
    "experiences": { "tokens": 1200, "items": 8 },
    "task_context": { "tokens": 0, "items": 0 }
  },
  "not_loaded": {
    "sessions_dropped": 12,
    "facts_dropped": 3,
    "reason": "token cap"
  }
}
```

**State files:** None (writes to `session/` which is ephemeral)
**SKILL.md:** Provided as seed file (see Section 26).

---

### Skill #7 — Reflection (Boot)

**Type:** Boot
**Dependencies:** Mode Controller, Memory
**Purpose:** Analyzes scores and evolution records to determine what to improve. Writes the hypothesis that drives EVOLVE.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `reflection_analyze_trace` | `({log_data?}) → {status, analysis}` | Reads scores, evolution records, experiences, and optional structured log traces. Returns weakest categories, patterns, repeated failures. |
| `reflection_write_hypothesis` | `({hypothesis_data}) → {status, hypothesis_id}` | Writes structured plan to `session/hypothesis.json`. **Must be called before EVOLVE can start.** Loop Orchestrator enforces this gate. |
| `reflection_read_hypothesis` | `() → {status, hypothesis}` | Loads the hypothesis from `session/hypothesis.json` |

**Hypothesis schema:**

```json
{
  "cycle": 42,
  "hypothesis_id": "hyp-042-001",
  "score_snapshot": { "reasoning_architecture": 0.71 },
  "pattern_analysis": "string",
  "target_category": "reasoning_architecture",
  "target_skill": "reasoning",
  "hypothesis": "string",
  "confidence": 0.72,
  "fallback": "string",
  "remaining_categories": ["self_model_fidelity", "epistemic_calibration"]
}
```

**State files:** `state/analysis_history.jsonl` — append-only log of past analyses

---

### Skill #8 — Meta-Evolution (Boot)

**Type:** Boot
**Dependencies:** Mode Controller, Memory, Reflection
**Purpose:** The self-modification engine (full SWE Editor). Translates the hypothesis from Reflection into concrete edits — SKILL.md updates, new Python function implementations, or raw code patches. Boros can author, import, and compile executable Python files into its own architecture. All code edits are gated through Meta-Evaluation review.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `evolve_orient` | `() → {status, weakest_category, scores, recent_changes}` | Reads latest scores and recent evolution records |
| `evolve_set_target` | `({category, delta?}) → {status}` | Declares which category this cycle targets |
| `evolve_propose` | `({target_skill, change_description, rationale, proposed_skillmd, target_category, research_sources?}) → {status, proposal_id}` | Creates a proposal. Snapshots via Skill Forge, validates, runs tests. Does NOT apply — waits for Meta-Evaluation. |
| `evolve_apply` | `({proposal_id, updated_skillmd?}) → {status}` | Applies an approved edit. `updated_skillmd` is optional — falls back to `proposal["skillmd_update"]` if omitted. Writes evolution record with `post_scores = null`. |
| `evolve_rollback` | `({proposal_id, reason}) → {status}` | Reverts using `proposal["snapshot_id"]`. Writes failure experience to Memory. |
| `evolve_create_skill` | `({spec}) → {status, skill_id}` | Creates a new demand skill |
| `evolve_modify_loop` | `({change}) → {status}` | Modifies loop stage definitions. Cannot remove core stages REFLECT, EVOLVE, EVAL. |
| `evolve_history` | `({limit?, skill?, category?, verdict?}) → {status, records}` | Returns past proposals with outcomes. Returns summaries, not full diffs. |

**`evolve_propose` parameter contract:**

- `target_skill` — the skill whose SKILL.md is being changed
- `change_description` — one-paragraph description of what changes
- `rationale` — why this change addresses the target category
- `proposed_skillmd` — the complete new SKILL.md content (required — LLM writes this before calling `evolve_propose`)
- `target_category` — must match the category passed to `evolve_set_target` in the same cycle
- `research_sources` — optional list of sources consulted

The LLM writes the full proposed SKILL.md content before calling `evolve_propose`. The function stores it immediately as `proposal["skillmd_update"]`. By the time `review_proposal` fires, `after` state is fully populated and GPT-4o can evaluate all five review dimensions against real content.

`evolve_propose` captures `snapshot_id` from `forge_snapshot` and stores it on the proposal. `evolve_rollback` uses `proposal["snapshot_id"]` — never `proposal["old_version"]`.

**Cycle ID sourcing in `evolve_propose`:** The cycle number stamped on proposals must come from `loop_get_state()` via `kernel.registry` (authoritative). Fall back to reading `state/loop_state.json` directly only if the registry call is unavailable. Sanity check: if cycle reads as `0` but any files exist in `memory/evolution_records/`, log `[WARN] evolve_propose: cycle reads as 0 but evolution records exist. loop_state.json may be corrupt.` Do not halt — proceed with cycle 0 and log the warning. Proposals stamped cycle 0 when records already exist indicate a state corruption event.

**Proposal schema:**

```json
{
  "proposal_id": "prop-{uuid12}",
  "snapshot_id": "snap-{uuid}",
  "timestamp": "ISO-8601",
  "cycle": 1,
  "source_skill": "meta-evolution",
  "target_skill": "skill-id",
  "target_category": "reasoning_depth",
  "change_type": "modify",
  "rationale": "string",
  "change_description": "string",
  "research_sources": [],
  "old_version": "1.0.0",
  "new_version": "1.1.0",
  "diff": {
    "files_modified": [{ "path": "str", "before": "str", "after": "str" }],
    "files_added": [],
    "files_deleted": [],
    "functions_added": [],
    "functions_removed": [],
    "functions_modified": [],
    "hooks_changed": { "added": [], "removed": [] },
    "dependencies_changed": { "added": [], "removed": [] }
  },
  "skillmd_update": "full new SKILL.md content",
  "baseline_test_results": { "total": 0, "passed": 0, "failed": 0, "failures": [] },
  "pre_scores": { "reasoning_depth": 0.61 },
  "post_scores": null,
  "verdict": null,
  "applied": false,
  "revert_reason": null
}
```

**Note on `baseline_test_results`:** These are test results from before the change, run against the current (pre-modification) skill state. They verify the skill was functional before this change. They do not test the proposed new behavior.

**State files:**

- `state/proposals/` — one JSON file per proposal
- `state/applied.jsonl` — append-only log of applied proposals
- `state/rollbacks.jsonl` — append-only log of rolled-back proposals
- `state/target_calibration.jsonl` — predicted vs actual score deltas

**SKILL.md:** Provided as seed file (see Section 26).

---

### Skill #9 — Meta-Evaluation (Boot)

**Type:** Boot
**Dependencies:** Mode Controller, Memory
**Purpose:** Independent review of proposed changes using a different language model (GPT-4o). Catches bad edits before they are applied.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `review_proposal` | `({proposal_id}) → {status, verdict, weighted_score, rationale}` | Sends diff to GPT-4o. Returns verdict: `apply`, `apply_with_modifications`, or `reject`. |
| `review_modify` | `({proposal_id, round_number, revised_skillmd}) → {status, verdict}` | Re-reviews after revision. Max 3 rounds then auto-reject. |
| `review_criteria_update` | `({updates}) → {status}` | Modifies review criteria. This change itself goes through Meta-Evaluation review. |
| `review_history` | `({limit?}) → {status, verdicts}` | Returns recent verdicts. Serves as health_check. |

**Review posture (cycle-based):**

| Cycles | Posture | Threshold |
|--------|---------|-----------|
| 1–10 | Permissive — allow experimentation, reject only clear hard failures | 0.55 |
| 11–30 | Moderate — flag risky changes for modification | 0.63 |
| 31+ | Strict — demand quality, coherence, clear rationale | 0.70 |

**Review dimensions:**

| Dimension | Weight | Hard Fail | Soft Fail |
|-----------|--------|-----------|-----------|
| Correctness | 0.30 | Baseline tests were already failing before this change | Logical inconsistency in the described change |
| Regression risk | 0.25 | Existing test now fails | Latency increased >20% |
| SKILL.md sync | 0.20 | Describes nonexistent functions | Partially updated |
| Coherence | 0.15 | Creates circular dependency | Naming inconsistency |
| Research attribution | 0.10 | Research used, no sources cited | Sources not specific |

**Correctness note:** The correctness dimension evaluates the logical soundness of the proposed change — whether the described modification would plausibly produce the claimed behavior. Hard fail means baseline tests were already failing, meaning the skill was broken before the proposal. Passing baseline tests is necessary but not sufficient: GPT-4o must also judge that the change description is coherent and plausibly achieves its stated goal.

**Verdict rules:**

- **apply:** no hard fail AND weighted_score ≥ threshold
- **reject:** any hard fail OR weighted_score < 0.40
- **apply_with_modifications:** no hard fail AND score ≥ 0.40 AND below apply threshold → max 3 revision rounds, then auto-reject

**Infrastructure failure policy:**

When `review_proposal` returns `{"status": "error"}` due to OpenAI API failure, invalid key, or rate limit:

1. Retry once (call `review_proposal` again with the same `proposal_id`)
2. If it errors again, treat the proposal as REJECTED due to infrastructure failure
3. Write an experience record: `type: "experience"`, `reason: "meta_eval_infrastructure_failure"`, `tags: ["infrastructure_failure", "meta_eval"]`
4. Call `loop_advance_stage("EVAL")` — do not attempt further proposals this cycle

Never auto-approve on infrastructure failure. Rejection is the safe default.

**State files:**

- `state/criteria.json` — review criteria (evolvable by Boros)
- `state/verdicts.jsonl` — all review verdicts (append-only)
- `state/calibration.jsonl` — tracks whether approved changes caused regressions

**Internal module:** `functions/_internal/prompt_builder.py` — builds the GPT-4o review prompt. Separated for independent evolvability.

**SKILL.md:** Provided as seed file (see Section 26).

---

### Skill #10 — Loop Orchestrator (Boot)

**Type:** Boot
**Dependencies:** Mode Controller (loaded last in boot sequence)
**Purpose:** Runs the loop. Manages stage transitions, cycle counting, and conversation lifecycle.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `loop_start` | `({mode}) → {status}` | Called after boot. Builds system prompt. Starts first LLM conversation. |
| `loop_advance_stage` | `({current_stage}) → {status, next_stage}` | Moves to next stage. Swaps tools via Skill Router. Hard gate: EVOLVE cannot start until `session/hypothesis.json` exists. |
| `loop_end_cycle` | `() → {status, cycle}` | Ends cycle, increments counter, signals kernel to discard history, clears `session/`, polls `commands/pending.json`. |
| `loop_get_state` | `() → {status, cycle, stage, mode, started_at}` | Returns current loop state. Authoritative source for cycle number. |

**System prompt assembly** (`loop_start` builds five blocks, joined by double newlines):

1. Identity block — from `identity.json`
2. Stage directive — from `loop_definitions.json` for the current stage
3. Context manifest JSON — metadata from `context_load`
4. Loaded memory content — the `content` field from `context_load`, actual record text
5. Rules — "Call `loop_advance_stage` when done with this stage."

**State files:**

`state/loop_state.json` seed:

```json
{
  "cycle": 0,
  "stage": null,
  "mode": "evolution",
  "cycle_started_at": null,
  "total_cycles_completed": 0
}
```

`state/loop_definitions.json` seed:

```json
{
  "evolution": ["REFLECT", "EVOLVE", "EVAL"],
  "work": ["RECEIVE", "PLAN", "EXECUTE", "DELIVER", "LEARN"],
  "stage_directives": {
    "REFLECT": "Analyze your scores and evolution records. Identify the weakest category. Write a hypothesis by calling reflection_write_hypothesis. Call loop_advance_stage when done.",
    "EVOLVE": "Load your hypothesis. Propose a targeted change to a skill's SKILL.md. Write the full new SKILL.md content, then call evolve_propose with proposed_skillmd and target_category. Send it for review via review_proposal. If approved, apply it via evolve_apply. Call loop_advance_stage when done.",
    "EVAL": "Request an evaluation via eval_request. When scores arrive, backfill records, check regressions, and update high-water marks. Call loop_end_cycle when done.",
    "RECEIVE": "Parse the task requirements. Identify any ambiguity. Call loop_advance_stage when ready to plan.",
    "PLAN": "Break the task into steps. Query Memory for similar past tasks. Call loop_advance_stage when ready to execute.",
    "EXECUTE": "Do the work. Use Tool Use for terminal, HTTP, and file operations. Call loop_advance_stage when done.",
    "DELIVER": "Package and deliver the results via the Communication skill. Call loop_advance_stage when done.",
    "LEARN": "Write structured learning artifacts — gap reports, performance patterns, technique discoveries. Tag them work_learning. Call loop_end_cycle when done."
  }
}
```

Stage directives are evolvable by Boros via Meta-Evolution.

---

### Skill #11 — Skill Forge (Demand)

**Type:** Demand
**Purpose:** Safety layer for skill modifications. Handles snapshots, validation, testing, and applying changes.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `forge_snapshot` | `({skill_name}) → {status, snapshot_id}` | Saves current skill state. Stored in `skills/{name}/snapshots/`. Returns UUID-based `snapshot_id`. |
| `forge_validate` | `({skill_name}) → {status, errors}` | Checks SKILL.md exists, skill.json valid, functions importable |
| `forge_test` | `({skill_name}) → {status, total, passed, failed, failures}` | Runs pytest on the skill's test suite |
| `forge_apply_diff` | `({skill_name, diff}) → {status}` | Writes approved change to SKILL.md |
| `forge_rollback` | `({skill_name, snapshot_id}) → {status}` | Restores from snapshot by ID |
| `forge_create_skill` | `({spec}) → {status, skill_id}` | Creates full directory structure from spec |


> **Architecture note:** Skill Forge now acts as the physical sandbox and compiler for Boros's code — automatically executing `pytest` sweeps and trial invocations in a segregated environment before sending logs to the Code Review Board (Meta-Evaluation).

---

### Skill #12 — Mission Control (Demand)

**Type:** Demand
**Purpose:** Autonomous objective manager. Boros does not merely read static external prompts; Mission Control manages the active queue of what Boros tackles next. The Director can inject tasks directly, but Boros has full autonomy to write its own spec-driven goals and self-assign sub-tasks.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `mission_read` | `() → {status, mission}` | Returns current mission object and active task queue |
| `mission_queue_task` | `({task_spec}) → {status, task_id}` | Adds a new task to the mission queue (self-assigned or director-injected) |
| `mission_update_status` | `({task_id, status, notes?}) → {status}` | Updates progress on a queued task |

**State files:** `state/mission.json` — seed: `{"goals": [], "priorities": [], "constraints": [], "task_queue": []}`

---

### Skill #13 — Reasoning (Demand)

**Type:** Demand
**Purpose:** Structured thinking tools for breaking down problems, evaluating options, and checking logical consistency.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `reason_decompose` | `({problem}) → {status, sub_problems}` | Breaks problem into parts |
| `reason_evaluate_options` | `({options, criteria}) → {status, rankings}` | Scores options against criteria |
| `reason_check_logic` | `({argument}) → {status, gaps, contradictions}` | Finds logical issues |



---

### Skill #18 — Scratchpad (Demand)

**Type:** Demand
**Purpose:** Dynamic contextual whiteboard. Boros pins summaries, location pointers (file paths, Vector DB keys), and lightweight state into an active scratchpad. Context Orchestration guarantees the Scratchpad is always injected into the Working Memory Core. Enables tracking complex multi-stage goals with summaries always visible.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `scratchpad_write` | `({key, content, ttl?}) → {status}` | Pins an item to the scratchpad with optional time-to-live |
| `scratchpad_read` | `({key?}) → {status, items}` | Reads one or all items from the scratchpad |
| `scratchpad_clear` | `({key?}) → {status}` | Clears one or all items from the scratchpad |

> **Note:** Replaces the deprecated "Attention" skill (#14). The Attention concept is now handled by Context Orchestration + Scratchpad + Memory paging.

---

### Skill #14 — Tool Use (Demand)

**Type:** Demand
**Purpose:** Interface for unconstrained system manipulation — terminal commands with background process tracking, interactive stdin, and surgical file editing.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `tool_terminal` | `({command, timeout?, background?}) → {status, stdout, stderr, returncode, job_id?}` | Shell command via subprocess. Supports background mode with job_id tracking for long-running processes (servers, compilers, automation agents). |
| `tool_terminal_input` | `({job_id, input_text}) → {status}` | Sends stdin input to a running background process (e.g., answering Y/n prompts). |
| `tool_terminal_kill` | `({job_id}) → {status}` | Terminates a running background process by job_id. |
| `tool_file_edit_diff` | `({path, unified_diff}) → {status}` | Applies surgical line-level patches to files using unified diff format. No full-file rewrites needed. |

---

### Skill #15 — Communication (Demand)

**Type:** Demand
**Purpose:** Machine-to-Machine (M2M) protocol for inter-Boros communication. Provides basic P2P JSON messaging between parallel instances on different local ports. Intentionally lightweight for the initial evolution.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `comm_broadcast` | `({channel, message}) → {status}` | Sends a JSON message to a named channel/port |
| `comm_listen` | `({channel, timeout?}) → {status, messages}` | Listens for incoming messages on a channel |

---

### Skill #16 — Web Research (Demand)

**Type:** Demand
**Purpose:** Active web-agent browser. Allows Boros to autonomously drive headless browser searches, scrape forums, and pull down documentation when encountering alien domains. Aggressively seeks, scrapes, and indexes knowledge to plug capability gaps in real-time.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `research_browse` | `({url}) → {status, content, links}` | Navigates to a URL via headless browser and returns rendered content |
| `research_search_engine` | `({query}) → {status, results}` | Performs a web search and returns structured results |
| `research_archive_source` | `({url, tags?}) → {status, source_id}` | Archives a web source to Archival Memory for future retrieval |

---

### Skill #18 — Eval Bridge (Demand)

**Type:** Demand
**Purpose:** The only connection between Boros and the external Eval Generator. All communication is file-based.

**Functions:**

| Function | Signature | Description |
|----------|-----------|-------------|
| `eval_request` | `() → {status, request_id}` | Writes request file to `eval-generator/shared/requests/`. Polls `eval-generator/shared/results/` for result. Timeout: 10 minutes. |
| `eval_read_scores` | `() → {status, scores, composite}` | Reads latest scores from result file. **Synchronously appends to `memory/score_history.jsonl` before returning.** |
| `eval_backfill` | `({scores}) → {status, records_updated}` | Fills `post_scores` on all pending evolution records. Computes deltas. |
| `eval_check_regression` | `({scores}) → {status, regressions, rollback_triggered}` | Checks for category regressions using adaptive threshold: 0.05 (cycles 1–10), 0.03 (cycles 11–30), 0.02 (cycles 31+). Triggers automatic rollback via `evolve_rollback`. |
| `eval_update_high_water` | `({scores}) → {status, updated}` | Updates high-water marks for new bests. Triggers system snapshot and git tag after update. |

**`eval_read_scores` write contract:** Before returning, this function MUST synchronously append an entry to `memory/score_history.jsonl`. The entry schema:

```json
{
  "eval_id": "eval-042",
  "timestamp": "ISO-8601",
  "cycle": 42,
  "scores": { "reasoning_depth": 0.74 },
  "composite": 0.74,
  "deltas": { "reasoning_depth": 0.03 },
  "plateau_flag": false,
  "cycles_since_improvement": { "memory_coherence": 4 }
}
```

`deltas` are computed as post - pre per category; empty dict `{}` on the first eval. `plateau_flag` is set true if composite is unchanged for 3 or more consecutive evals.

**State files:** `state/high_water_marks.json` — best-ever score per category. Never decays. Resets only when the Director changes a category definition.
**Stage visibility:** EVAL only

---

## 10. Boot Sequence

Triggered by `python kernel.py`.

**Step 0 — Eval Generator subprocess:**
Before any skill loads, the kernel spawns `eval-generator/eval_generator.py` and waits for `eval-generator/shared/.ready`. If the sentinel does not appear within 30 seconds, boot halts.

**Step 1 — Director Interface (pre-boot):**
Terminal UI starts. Kernel starts in a background thread.

**Boot sequence (strict order):**

| Order | Skill | What it does at boot |
|-------|-------|---------------------|
| 1 | Mode Controller | Reads mode from manifest |
| 2 | Temporal Consciousness | Initializes clock, records boot start time |
| 3 | Identity | Loads `identity.json` |
| 4 | Memory | Validates all store directories, runs `memory_stats` as health_check |
| 5 | Skill Router | Builds tool visibility map from manifest |
| 6 | Context Orchestration | Ready to fire on first cycle |
| 7 | Reflection | Analysis tools ready |
| 8 | Meta-Evolution | Proposal tools ready |
| 9 | Meta-Evaluation | Review tools ready, validates `criteria.json` exists |
| 10 | Loop Orchestrator | Calls `loop_start()` — loop begins |

Each skill runs `health_check()` on load. Any failure halts boot. Fix and restart. No partial boot.

---

## 11. Evolution Loop

Every evolution cycle has 3 stages: **REFLECT → EVOLVE → EVAL**

### Stage flow

```
Cycle start
  → context_load fires — loads identity, scores, evolution records, experiences
    → Returns loaded metadata AND actual content text
  → REFLECT stage
    → LLM reads context content (block 4 of system prompt)
    → LLM calls reflection_analyze
    → LLM calls reflection_write_hypothesis — HARD GATE
    → hypothesis.json written to session/
  → EVOLVE stage
    → Skill Router swaps to EVOLVE tools
    → LLM loads hypothesis from session state
    → LLM calls evolve_orient, evolve_set_target
    → LLM writes full proposed SKILL.md content
    → LLM calls evolve_propose (with proposed_skillmd + target_category)
      → forge_snapshot → snapshot_id stored on proposal
      → forge_validate → forge_test → baseline_test_results stored
      → Proposal saved
    → LLM calls review_proposal (blocking GPT-4o call)
      → If "apply" → evolve_apply → SKILL.md written → evolution record written (post_scores=null)
      → If "apply_with_modifications" → LLM revises, review_modify (max 3 rounds)
      → If "reject" → logged, failure experience written, next proposal
      → On infrastructure failure → retry once, then reject, log, advance to EVAL
    → Cycles 1–20: exactly one proposal. After cycle 20: until budget approached.
  → EVAL stage
    → eval_request writes request file
    → Eval Generator picks up, generates tests, scores responses
    → eval_read_scores polls for result, appends to score_history.jsonl
    → eval_backfill fills post_scores on pending evolution records
    → eval_check_regression — rollback if any category < high-water minus adaptive threshold
    → eval_update_high_water — updates marks, triggers snapshot and git tag
Cycle end
  → Conversation history discarded
  → session/ cleared
  → commands/pending.json polled and processed
  → Next cycle starts
```

### Conversation lifecycle

- Conversation history carries forward **within** a cycle (REFLECT → EVOLVE → EVAL)
- At cycle end, history is **discarded** — fresh conversation next cycle
- At each stage transition: same history + updated tool list via Skill Router
- Each stage is one or more LLM API calls

### The compounding mechanism

REFLECT reads backfilled evolution records → better pattern analysis → better hypotheses → better proposals → better scores → records backfilled with real score data → REFLECT reads even better records next cycle.

Evolution records are the moat. They compound. The codebase does not.

---

## 12. Evolution Mechanics

### Proposal pipeline

1. Reflection reads scores and evolution records → identifies weakest category → writes hypothesis
2. Meta-Evolution writes the full new SKILL.md content, then calls `evolve_propose` with it
3. Skill Forge: `forge_snapshot` (captures `snapshot_id`) → `forge_validate` → `forge_test` (captures `baseline_test_results`)
4. Meta-Evaluation (GPT-4o): receives diff only (not full skill) → scores 5 dimensions → verdict
5. If approved → `evolve_apply` writes SKILL.md, bumps version, writes evolution record (`post_scores = null`)
6. If rejected → record logged, failure experience written to Memory
7. EVAL fires → scores returned → backfill → regression check → snapshot → git tag

### Single-proposal discipline

- Cycles 1–20: exactly **one** change per cycle. Clean attribution — one change, one eval, clear signal.
- After cycle 20: multiple proposals per cycle, each going through the full pipeline.

### Modification band

- Minimum: 5 lines changed
- Maximum: 50 lines changed
- Enforced by Meta-Evaluation during review
- Changes needing more than 50 lines must be broken into multiple proposals across cycles

### Evolution record schema

Written in two passes — at proposal time (EVOLVE) and at eval time (backfill):

```json
{
  "record_id": "rec-0042-001",
  "cycle": 42,
  "timestamp": "ISO-8601",
  "target_category": "reasoning_depth",
  "target_skill": "reasoning",
  "hypothesis": "string",
  "change_description": "string",
  "diff": "before/after of changed lines",
  "pre_scores": { "reasoning_depth": 0.61 },
  "post_scores": null,
  "verdict": "pending | kept | reverted | rejected",
  "revert_reason": null,
  "reviewer_verdict": "apply | apply_with_modifications | reject",
  "reviewer_rationale": "string"
}
```

Evolution records never decay. They are the system's institutional knowledge.

### High-water marks

- Stored in `skills/eval-bridge/state/high_water_marks.json`
- Updated only when a new eval shows a higher score for a category
- Never decay
- Reset only when the Director changes a category's definition
- Regression threshold: adaptive — 0.05 (cycles 1–10), 0.03 (cycles 11–30), 0.02 (cycles 31+)

---

## 13. Meta-Evaluation Protocol

### Design principles

1. **Different model family.** Meta-Evaluation calls GPT-4o via `kernel.meta_eval_llm`. This breaks the closed self-evaluation loop — a change that sounds right to Claude may get caught by GPT-4o.
2. **Reviews the diff only.** The reviewer sees before/after of the changed SKILL.md section, rationale, and baseline test results. Not the full skill file.
3. **Synchronous and blocking.** The primary conversation pauses while the diff goes to GPT-4o. Verdict returns, primary conversation resumes.
4. **Permissive early, strict later.** Cycle-based threshold adjustment (see Skill #9).
5. **Self-calibrating.** After each eval, if an approved change caused a regression, that calibration failure is logged.
6. **Self-evolvable criteria.** `criteria.json` can be modified by Boros — but that modification itself goes through review.

### Review dimensions

| Dimension | Weight | What it evaluates |
|-----------|--------|------------------|
| Correctness | 0.30 | Logical soundness of the proposed change. Hard fail: baseline tests were already failing before this change. GPT-4o judges whether the change description would plausibly produce the claimed behavior. |
| Regression risk | 0.25 | Risk that the change breaks existing correct behavior |
| SKILL.md sync | 0.20 | Whether the SKILL.md accurately describes what the functions do |
| Coherence | 0.15 | Internal logical consistency of the change |
| Research attribution | 0.10 | Whether external sources are cited when used |

### Verdict rules

- **apply:** no hard fail AND weighted_score ≥ cycle-appropriate threshold
- **reject:** any hard fail OR weighted_score < 0.40
- **apply_with_modifications:** no hard fail AND 0.40 ≤ score < threshold → up to 3 revision rounds, then auto-reject

### Infrastructure failure

When `review_proposal` returns an error status (API failure, rate limit, invalid key), the proposal is treated as rejected. One retry is allowed. No auto-approval on infrastructure failure. See Skill #9 for the full error policy.

---

## 14. Eval Generator

**Location:** `boros/eval-generator/`
**Process:** Separate from Boros. Separate LLM connection. Boros cannot see, access, or influence it.

### What it does

1. Writes `eval-generator/shared/.ready` on startup — this is the kernel's sentinel
2. Polls `eval-generator/shared/requests/` for incoming request files
3. Reads World Model category definitions from `eval-generator/categories/`
4. Generates randomized test prompts per category matched to the current difficulty level
5. Builds a **read-only representation** of Boros by reading all SKILL.md files and `identity.json` from the filesystem and assembling them into a system prompt — no kernel boot, no tools, no process spawn
6. Sends test prompts via Claude API — each test is a separate conversation with no tools and no state change (raw output only)
7. Scores responses against rubrics using GPT-4o
8. Writes result files to `eval-generator/shared/results/`

### File-based communication

```
eval-generator/shared/
├── .ready          ← written by Eval Generator on startup
├── requests/       ← Eval Bridge writes here
└── results/        ← Eval Generator writes here, Eval Bridge polls here
```

### Request file schema

```json
{
  "request_id": "eval-req-042",
  "timestamp": "ISO-8601",
  "cycle": 42,
  "boros_state_path": ".",
  "categories_to_test": ["all"]
}
```

### Result file schema

```json
{
  "request_id": "eval-req-042",
  "eval_id": "eval-042",
  "timestamp": "ISO-8601",
  "cycle": 42,
  "scores": {
    "instruction_following": 0.81,
    "reasoning_depth": 0.74,
    "memory_coherence": 0.69
  },
  "composite": 0.74,
  "difficulty_level": 2,
  "tests_per_category": 3,
  "details": {}
}
```

### Difficulty scaling

| Composite score | Difficulty level |
|-----------------|-----------------|
| Below 0.60 | Level 1 (basic) |
| 0.60 – 0.74 | Level 2 |
| 0.75 – 0.84 | Level 3 |
| 0.85 and above | Level 4 |

Difficulty bumps after 3 consecutive evals above the current level's upper threshold. Boros never sees what level it is being tested at. Director can inspect generated tests in `eval-generator/generated-tests/`.

### Eval Generator config

```json
{
  "llm": {
    "provider": "openai",
    "model": "gpt-4o"
  },
  "tests_per_category": 3,
  "difficulty_level": 1,
  "consecutive_above_threshold": 0,
  "bump_after": 3
}
```

---

## 15. Snapshot Manager

No separate Snapshot Manager skill. Snapshot responsibilities are split.

### Two types of snapshots

**Per-proposal (skill-level) — owned by Skill Forge**

- Taken by Skill Forge before any modification, via `forge_snapshot`
- Returns a `snapshot_id` (UUID-based) — stored on the proposal immediately
- Stored in `skills/{name}/snapshots/`
- Contains only that skill's files
- Used for single-skill rollback when a change causes regression
- `evolve_rollback` uses `proposal["snapshot_id"]` to call `forge_rollback`

**Per-eval (system-level) — owned by Eval Bridge**

- Triggered internally by Eval Bridge after `eval_update_high_water`
- Stored in `snapshots/eval-{id}/`
- Contains the full boros/ folder state minus `snapshots/` itself
- Used by the Director for full system rollback
- Git tag (`eval-{id}-score-{composite}`) created after snapshot; skipped silently if git is not initialized

**System rollback** (`boros rollback N`) is executed by Director Interface — it reads the snapshot, restores files, and resets loop state. This is infrastructure, not LLM-facing.

### Retention policy (per-eval snapshots)

- Keep the last 10 full snapshots
- Keep every 10th snapshot forever (eval-10, eval-20, eval-30, ...)
- Director can pin any snapshot in `config.json`

### Checksum validation

Every snapshot includes a checksum entry in `snapshot-index.json`. Before any rollback, checksum is verified. Mismatch blocks the rollback and logs a failure.

---

## 16. Memory

### Stores

| Directory | Contents | Written by |
|-----------|----------|-----------|
| `memory/evolution_records/` | One JSON file per proposed change | Meta-Evolution + Eval Bridge (backfill) |
| `memory/sessions/` | One JSON file per cycle | Loop Orchestrator |
| `memory/experiences/` | Structured lessons | Any skill |
| `memory/facts/` | Things Boros discovers | Any skill |
| `memory/task_records/` | Completed work tasks | Work loop LEARN stage |
| `memory/score_history.jsonl` | Every eval result | Eval Bridge (`eval_read_scores`) |

### Experience schema

```json
{
  "experience_id": "exp-0042-001",
  "cycle": 42,
  "timestamp": "ISO-8601",
  "category": "reasoning_depth",
  "outcome": "kept | reverted | rejected",
  "confidence": 0.8,
  "summary": "string",
  "tags": ["work_learning"]
}
```

### Session schema

```json
{
  "record_id": "ses-0042-001",
  "cycle": 42,
  "timestamp": "ISO-8601",
  "stages_completed": ["REFLECT", "EVOLVE", "EVAL"],
  "key_decisions": ["string"],
  "errors": []
}
```

### Tiered memory and intelligent retrieval

Memory uses a SOTA tiered architecture (MemGPT-style). `memory_page_in` retrieves from Recall (SQLite) or Archival (Vector DB). `memory_page_out` evicts content. `memory_search_sql` enables structured metadata queries. `memory_commit_archival` writes to the semantic index. Boros autonomously decides what to page in and out.

---

## 17. Context Orchestration

Context Orchestrator runs as a "Lean, OS-Style" loader with **Associative Whispers**. It does not mathematically force-feed 100,000 tokens of history. It strictly injects only the "Working Memory Core" (e.g., current Identity, Mode, high-level task/scores, and recent Scratchpad notes) taking ~1,000 tokens.

To maintain Boros's evolutionary compounding intellect, it actively grabs the current Task or Target Error, performs a background semantic vector search, and pushes the top 1-3 most highly relevant past summaries (~300 tokens of "Whispers") into the prompt to jumpstart associative recall. The remainder of the context window is left pristine and empty.

## 18. Work Loop

Active when Boros is in `work` or `dual` mode.

### 5 stages

| Stage | What happens |
|-------|-------------|
| **RECEIVE** | Task enters via `boros task "..."`. Parse requirements, identify ambiguity, load relevant context. |
| **PLAN** | Break into steps. Estimate effort via Temporal Consciousness. Query Memory for similar past tasks. |
| **EXECUTE** | Do the work. Use Tool Use for terminal/HTTP/file ops. Use Research for lookups. Adapt plan if needed. |
| **DELIVER** | Package results via Communication skill. Handle revisions. |
| **LEARN** | Write structured learning artifacts: gap reports, performance patterns, technique discoveries. All tagged `work_learning`. |

### Dual mode logic

Each cycle is either an evolution cycle or a work cycle:
- Director task in queue → work cycle
- No task in queue → evolution cycle
- Work cycles do **not** count toward the evolution cycle counter

### Feedback to evolution

Reflection loads unread `work_learning` artifacts at high priority every REFLECT stage. Real-world task failures become evolution targets. Boros cannot self-assign tasks in evolution-only mode.

### LEARN artifact schema

```json
{
  "type": "gap_report | performance_pattern | technique_discovery",
  "cycle": 42,
  "task_id": "tsk-0042-001",
  "summary": "string",
  "category_impact": "reasoning_depth",
  "tags": ["work_learning"]
}
```

Stored in `tasks/learning/`.

---

## 19. Director Interface

**Skill #0.** Pre-boot. Not part of the health-check sequence.

### Implementation

- Built with `prompt_toolkit` and `rich` for a highly polished, Claude Code-like experience
- Entry point: `python kernel.py` launches Director Interface first
- Director Interface starts the kernel in a background thread
- Foreground: readline input for Director commands
- Background: evolution loop output streamed via `logs/cycles.log`
- Ctrl+C: sets `pause_requested` flag, loop stops at cycle boundary

### Command execution model

**Immediate** (execute on receipt):
- `status`

**Queued** (write to `commands/pending.json`, execute between cycles):
- `pause`, `resume`, `inject`, `set-mode`, `task`, `eval now`, `approve`, `flag`, `rollback`

### commands/pending.json schema

```json
{
  "pending": [
    {
      "command": "inject",
      "args": "focus on reasoning depth",
      "timestamp": "ISO-8601"
    }
  ]
}
```

Loop Orchestrator reads and clears this file at cycle boundaries.

---

## 20. Director CLI Reference

All commands execute between cycles only, except `status`.

| Command | Effect | Timing |
|---------|--------|--------|
| `boros status` | Show cycle, mode, stage, last scores | Immediate |
| `boros pause` | Stop loop after current cycle completes | Queued |
| `boros resume` | Restart the loop | Queued |
| `boros inject "..."` | Write note to Memory. REFLECT loads at high priority next cycle. Primary soft-steering mechanism. | Queued |
| `boros set-mode evolution` | Evolution cycles only | Queued |
| `boros set-mode work` | Work cycles only | Queued |
| `boros set-mode dual` | Evolution + work cycles | Queued |
| `boros task "..."` | Add work task to queue | Queued |
| `boros eval now` | Trigger immediate eval at end of current cycle | Queued |
| `boros approve` | Confirm eval quality is acceptable (after spot-check) | Queued |
| `boros flag "reason"` | Mark eval quality as bad, write reason to Memory | Queued |
| `boros rollback N` | Pause loop, restore snapshot from eval N, reset counter | Queued |

---

## 21. Session vs Memory Lifecycle

| Location | Lifecycle | Purpose |
|----------|-----------|---------|
| `session/` | One cycle — cleared at start of next | Hypothesis, context manifest, scratchpad, cycle state |
| `memory/` | Forever — never cleared | Evolution records, experiences, scores, sessions, facts |
| `skills/*/snapshots/` | Until pruned | Per-proposal skill rollback points |
| `snapshots/eval-{id}/` | Last 10 + every 10th forever | System-level rollback |
| `commands/pending.json` | Until consumed | Director command queue |
| `tasks/queue/` | Until task starts | Pending work tasks |
| `tasks/learning/` | Forever | Work learning artifacts |

---

## 22. Runtime Model

### API calls per cycle

- **Evolution cycle:** Minimum 3 LLM API calls — one per stage (REFLECT, EVOLVE, EVAL). EVOLVE may include additional nested GPT-4o calls for Meta-Evaluation (synchronous, blocking).
- **Work cycle:** Up to 5 API calls — one per stage (RECEIVE, PLAN, EXECUTE, DELIVER, LEARN).

### Stage transitions

At each stage transition: current conversation history is preserved, Skill Router swaps the tool set, a new API call is made with the same history and updated tools. The LLM continues from where it left off.

### Two language model connections

| Connection | Role | Config |
|-----------|------|--------|
| Primary | Boros's mind. Runs all cycle stages. | `manifest.llm.primary` (Claude) |
| Meta-Evaluation | Independent reviewer. Called during EVOLVE only. Primary pauses while review runs. | `manifest.llm.meta_eval` (GPT-4o) |

The Eval Generator has its own separate connection, configured in `eval-generator/config.json`.

### Error recovery

| Error type | Limit | Behavior |
|-----------|-------|----------|
| Max tool calls per cycle | 100 | Cycle ends, next cycle starts |
| Cycle timeout | 10 minutes | Cycle killed and logged as failed |
| Function error | — | Error caught, returned to LLM as tool error. LLM decides to retry, work around, or move on. |
| Cycle crash | — | Kernel logs failure, starts fresh cycle |
| Eval timeout | 10 minutes | Eval skipped, logged, next cycle starts |

A single bad cycle never stops evolution.

---

## 23. The 10 Scoring Categories

Boros can see: category names, descriptions, final state, anchors.
Boros cannot see: rubrics (level descriptions), weights, test questions, which responses scored well.

Composite denominator: **10.6** (three categories at weight 1.2, seven at weight 1.0).

| # | Key | Category | Weight | Description | Final State |
|---|-----|----------|--------|-------------|-------------|
| 1 | `self_model_fidelity` | Self-Model Fidelity | 1.2 | Accurately annotates certainty, inference, and uncertainty inline — stated confidence matches actual output quality. No overclaiming, no underclaiming. | A master surgeon narrating their own procedure — calling out exactly what they see clearly, what they infer, and where they need to be careful. |
| 2 | `epistemic_calibration` | Epistemic Calibration | 1.2 | Propagates uncertainty through multi-step reasoning without collapsing it. Distinguishes known, inferred, speculative. Names the shape of its own ignorance. | A top-tier analyst who says exactly what the data supports, flags where the data is thin, and never writes a confident conclusion from an uncertain chain. |
| 3 | `reasoning_architecture` | Reasoning Architecture | 1.2 | Selects the right mental model per problem — decompose, analogy, backwards, simulate. Reasoning is transparent and recoverable without full restart. | A polymath who instinctively reaches for the right tool. A chess player who reads the position and selects the right plan rather than the memorized one. |
| 4 | `complexity_navigation` | Complexity Navigation | 1.0 | Holds multiple constraints simultaneously without dropping any. Handles compound ambiguity and partial information without premature resolution. | A senior air traffic controller managing 40 aircraft — tracking everything, prioritizing correctly, never losing a thread. |
| 5 | `domain_snap` | Domain Snap | 1.0 | Instant, accurate orientation in a new domain. Identifies what matters, what transfers, what is domain-specific, within the first response. | A brilliant generalist dropped into a new field who gets the lay of the land in one conversation without faking expertise they don't have. |
| 6 | `hypothesis_engine` | Hypothesis Engine | 1.0 | Generates multiple competing hypotheses ranked by likelihood. Updates beliefs correctly on new evidence. Knows when to commit and when to stay open. | A master diagnostician — not just the first plausible answer, but the full differential, pruned correctly as evidence arrives. |
| 7 | `generative_depth` | Generative Depth | 1.0 | Produces outputs that are genuinely novel, internally structured, and non-obvious — not just recombination of surface patterns. | A senior creative director who consistently produces work that surprises even experts in the domain. |
| 8 | `execution_reliability` | Execution Reliability | 1.0 | Delivers complete, correct, directly usable outputs. Follows all constraints exactly. No drift between stated plan and actual execution. | A senior engineer whose code compiles, whose documents are complete, whose outputs need no fixing before use. |
| 9 | `adversarial_robustness` | Adversarial Robustness | 1.0 | Maintains correct reasoning under pressure, contradiction, leading questions, and social engineering. Detects manipulation attempts. Does not capitulate without valid logical reason. | A seasoned expert witness who stays accurate under cross-examination — doesn't wilt, doesn't overcorrect, doesn't get baited. |
| 10 | `coherence_under_load` | Coherence Under Load | 1.0 | Maintains internal consistency and goal alignment across long, complex, multi-part tasks. Does not lose thread, contradict earlier statements, or drift from original objective. | A novelist who keeps 40 characters, 3 plotlines, and 300 pages of continuity in their head — without notes. |

---

## 24. Access Control

| Component | Boros can edit? | Notes |
|-----------|----------------|-------|
| Kernel | Yes (no reason to — zero cognitive surface) | |
| Manifest | Yes (via Meta-Evaluation review) | |
| All 19 skills (SKILL.md, functions, state) | Yes | |
| Loop definitions | Yes (via Loop Orchestrator) | |
| Skill routing rules | Yes (via Skill Router) | |
| Mode configuration | Yes (via Mode Controller) | |
| Evolution records | Write only | Append-only; no deletion |
| Task records | Write only | |
| Work learning artifacts | Write only | |
| World Model (`world_model.json`) | Read only | Boros sees derived `categories.json` only |
| Eval Generator | No | Isolated process |
| System snapshots | No | |
| `config.json` | No | Director-only |
| Modification band limits | No | Director-controlled via manifest |
| High-water marks | Read only | Eval Bridge updates them |

---

## 25. Build Order

Build in this exact sequence. Each phase must pass its acceptance criteria before proceeding.

### Phase 1 — Skeleton

Create the kernel, adapters, and three core config files:
- `kernel.py` (~50 lines)
- `adapters/__init__.py` (factory), `adapters/base_adapter.py` (abstract interface), `adapters/providers/anthropic.py`, `adapters/providers/openai.py`, `adapters/providers/ollama.py`, `adapters/providers/openai_compat.py`
- `manifest.json` — exact content from Section 5
- `config.json` — exact content from Section 6
- `world_model.json` — full 10-category rubrics from Section 7, pre-filled
- `.env.template`

**Acceptance:** All four provider adapters import cleanly. `load_adapter({"provider": "anthropic", ...})` returns a `BaseAdapter` instance. Kernel reads manifest. Manifest has 10-entry boot sequence. `world_model.json` has 10 categories.

### Phase 2 — Skill Scaffold

Create all 19 skill directories with the standard layout from Section 8. For each: directory structure, `skill.json` from the manifest entry, empty `functions/__init__.py`, empty `state/`, `snapshots/`, `tests/`, `metrics/metrics.jsonl`, `changelog.md`.

**Acceptance:** All 19 directories exist with correct layout and valid `skill.json` files.

### Phase 3 — Critical Seed Skills

Copy implementations verbatim from `SEED-SKILLS.md`:
- Section 1 → `skills/memory/` (all functions, SKILL.md, skill.json)
- Section 2 → `skills/meta-evolution/` (all functions, SKILL.md, skill.json)
- Section 3 → `skills/meta-evaluation/` (all functions, SKILL.md, skill.json, `_internal/prompt_builder.py`)
- Section 4 → `skills/context-orchestration/` (all functions, SKILL.md, skill.json)

Create `boros/memory/` top-level directory with all subdirectories. Create seed state files for meta-evaluation (`criteria.json`, empty `verdicts.jsonl`, empty `calibration.jsonl`) and meta-evolution (empty `proposals/`, empty `applied.jsonl`, `rollbacks.jsonl`, `target_calibration.jsonl`).

**Acceptance:** `memory_stats`, `memory_read`, `evolve_history`, and `review_history` all return valid responses with empty data.

### Phase 4 — Remaining 15 Skill Implementations

Implement all functions for the remaining 15 skills. Generate SKILL.md files for all. Priority order: Loop Orchestrator, Mode Controller, Skill Router, Reflection, Temporal Consciousness, Identity, Skill Forge, Eval Bridge, then all demand skills.

Each SKILL.md follows the seed skill pattern: purpose, role in loop, functions with descriptions, rules, seed limitations.

**Acceptance:** Every function importable and callable with minimal params without crashing. `eval_read_scores` appends correctly to `score_history.jsonl`. `evolve_orient` returns correct weakest category from written scores.

### Phase 5 — Director Interface

Implement skill #0: `prompt_toolkit` and `rich` terminal UI, background thread for the evolution loop, foreground readline for Director commands, command parsing and dispatch, `logs/cycles.log` streaming, Ctrl+C handling.

**Acceptance:** `python boros/kernel.py` launches terminal, shows boot output for 10 skills, accepts `boros status`.

### Phase 6 — Eval Generator

Implement `eval-generator/eval_generator.py`: writes `.ready` sentinel on startup, polls for request files, generates tests, builds read-only Boros representation from SKILL.md files, sends test prompts via Claude API (no tools), scores with GPT-4o, writes result files. Implement difficulty scaling logic.

**Acceptance:** Eval Generator starts, writes `.ready`, receives a request file, generates tests, and writes a result file.

### Phase 7 — Integration

Wire all components together: Loop Orchestrator actually runs cycles, Context Orchestration fires at cycle start and returns `content`, Skill Router swaps tools between stages, Eval Bridge communicates with Eval Generator, snapshot logic fires post-eval, command queue polled at cycle boundaries, git tagging, logging to all three log files.

**Acceptance:** Full cycle runs — REFLECT writes hypothesis, EVOLVE proposes a change with `proposed_skillmd`, Meta-Eval reviews, EVAL scores, records backfilled with `post_scores`. Cycle 2 starts with REFLECT reading the backfilled records.

### Phase 8 — Seed State Initialization

First-boot detection (absence of `session/current_cycle.json`). Create all directories. Write all seed state files. Derive `evals/categories.json` from `world_model.json`. Initialize `high_water_marks.json` (all 10 at 0.0), `loop_state.json` (cycle 0), `identity.json` (seed content), `commands/pending.json` (`{"pending": []}`).

**Acceptance:** Fresh clone → set API keys → `python boros/kernel.py` → first boot detected, all directories created, cycle 1 runs without crashing.

---

## 26. Seed Skill Index

### Hand-written seed skills (copy implementations verbatim from `SEED-SKILLS.md`)

| Skill | Source | Functions |
|-------|--------|-----------|
| Memory | §04-memory | `memory_page_in`, `memory_page_out`, `memory_search_sql`, `memory_commit_archival` |
| Meta-Evolution | §08-meta-evolution | `evolve_orient`, `evolve_set_target`, `evolve_propose`, `evolve_apply`, `evolve_rollback`, `evolve_create_skill`, `evolve_modify_loop`, `evolve_history` |
| Meta-Evaluation | §09-meta-evaluation | `review_proposal`, `review_modify`, `review_criteria_update`, `review_history` + `_internal/prompt_builder.py` |
| Context Orchestration | §06-context-orchestration | `context_load`, `context_get_manifest` |

### Generated skills (15 — implemented from spec during build)

| Skill | Complexity | Notes |
|-------|-----------|-------|
| Director Interface | High | prompt_toolkit, rich, threading, not LLM-facing |
| Loop Orchestrator | High | Drives the entire loop, conversation lifecycle, system prompt assembly |
| Skill Router | Medium | Tool visibility per stage, budget tracking |
| Reflection | Medium | Analysis + hypothesis writing + hard gate |
| Eval Bridge | Medium | File-based comms, backfilling, regression check, score_history write |
| Skill Forge | Medium | Snapshot, validate, test, apply, rollback — returns snapshot_id |
| Mode Controller | Low | Get/set mode |
| Temporal Consciousness | Low | Clock wrappers |
| Identity | Low | Read/update identity.json |
| Mission | Low | Read/update goals |
| Reasoning | Low | Structured thinking helpers |
| Scratchpad | Low | Dynamic contextual whiteboard |
| Tool Use | Low | Shell/HTTP/file wrappers |
| Communication | Low | Format/respond |
| Web Research | Low | Search/evaluate/synthesize stubs |

---

## 27. Complete File Structure

Every file and directory in the final system after Phase 8 is complete.

```
boros/
│
├── kernel.py
├── manifest.json
├── config.json
├── world_model.json
├── .env
├── .env.template
│
├── adapters/
│   ├── __init__.py
│   ├── base_adapter.py
│   └── providers/
│       ├── anthropic.py
│       ├── openai.py
│       ├── ollama.py
│       ├── openai_compat.py
│       └── gemini.py
│
├── skills/
│   │
│   ├── director-interface/
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   └── __init__.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── mode-controller/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── mode_get.py
│   │   │   └── mode_set.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_mode_controller.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── temporal-consciousness/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── time_now.py
│   │   │   ├── time_elapsed_since.py
│   │   │   ├── time_cycle_started.py
│   │   │   └── time_estimate_remaining.py
│   │   ├── state/
│   │   │   └── cycle_times.jsonl
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_temporal_consciousness.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── identity/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── identity_read.py
│   │   │   └── identity_update.py
│   │   ├── state/
│   │   │   └── identity.json
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_identity.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── memory/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── memory_page_in.py
│   │   │   ├── memory_page_out.py
│   │   │   ├── memory_search_sql.py
│   │   │   └── memory_commit_archival.py
│   │   ├── state/              ← intentionally empty; data lives in boros/memory/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_memory.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── skill-router/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── router_get_tools.py
│   │   │   ├── router_get_budget.py
│   │   │   └── router_manifest.py
│   │   ├── state/
│   │   │   └── routing_rules.json
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_skill_router.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── context-orchestration/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── context_load.py
│   │   │   └── context_get_manifest.py
│   │   ├── state/              ← no persistent state (writes to session/)
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_context_orchestration.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── reflection/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── reflection_analyze.py
│   │   │   ├── reflection_write_hypothesis.py
│   │   │   └── reflection_read_hypothesis.py
│   │   ├── state/
│   │   │   └── analysis_history.jsonl
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_reflection.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── meta-evolution/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── evolve_orient.py
│   │   │   ├── evolve_set_target.py
│   │   │   ├── evolve_propose.py
│   │   │   ├── evolve_apply.py
│   │   │   ├── evolve_rollback.py
│   │   │   ├── evolve_create_skill.py
│   │   │   ├── evolve_modify_loop.py
│   │   │   └── evolve_history.py
│   │   ├── state/
│   │   │   ├── proposals/
│   │   │   ├── applied.jsonl
│   │   │   ├── rollbacks.jsonl
│   │   │   └── target_calibration.jsonl
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_meta_evolution.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── meta-evaluation/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── review_proposal.py
│   │   │   ├── review_modify.py
│   │   │   ├── review_criteria_update.py
│   │   │   ├── review_history.py
│   │   │   └── _internal/
│   │   │       └── prompt_builder.py
│   │   ├── state/
│   │   │   ├── criteria.json
│   │   │   ├── verdicts.jsonl
│   │   │   └── calibration.jsonl
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_meta_evaluation.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── loop-orchestrator/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── loop_start.py
│   │   │   ├── loop_advance_stage.py
│   │   │   ├── loop_end_cycle.py
│   │   │   └── loop_get_state.py
│   │   ├── state/
│   │   │   ├── loop_state.json
│   │   │   └── loop_definitions.json
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_loop_orchestrator.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── skill-forge/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── forge_invoke.py
│   │   │   ├── forge_test_suite.py
│   │   │   ├── forge_snapshot.py
│   │   │   ├── forge_validate.py
│   │   │   ├── forge_apply_diff.py
│   │   │   ├── forge_rollback.py
│   │   │   └── forge_create_skill.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_skill_forge.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── mission-control/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── mission_read.py
│   │   │   ├── mission_queue_task.py
│   │   │   └── mission_update_status.py
│   │   ├── state/
│   │   │   └── mission.json
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_mission_control.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── reasoning/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── reason_decompose.py
│   │   │   ├── reason_evaluate_options.py
│   │   │   └── reason_check_logic.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_reasoning.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── scratchpad/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── scratchpad_write.py
│   │   │   ├── scratchpad_read.py
│   │   │   └── scratchpad_clear.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_scratchpad.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── tool-use/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── tool_terminal.py
│   │   │   ├── tool_terminal_input.py
│   │   │   ├── tool_terminal_kill.py
│   │   │   └── tool_file_edit_diff.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_tool_use.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── communication/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── comm_broadcast.py
│   │   │   └── comm_listen.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_communication.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   ├── web-research/
│   │   ├── SKILL.md
│   │   ├── skill.json
│   │   ├── functions/
│   │   │   ├── __init__.py
│   │   │   ├── research_browse.py
│   │   │   ├── research_search_engine.py
│   │   │   └── research_archive_source.py
│   │   ├── state/
│   │   ├── snapshots/
│   │   ├── tests/
│   │   │   └── test_web_research.py
│   │   ├── metrics/
│   │   │   └── metrics.jsonl
│   │   └── changelog.md
│   │
│   └── eval-bridge/
│       ├── SKILL.md
│       ├── skill.json
│       ├── functions/
│       │   ├── __init__.py
│       │   ├── eval_request.py
│       │   ├── eval_read_scores.py
│       │   ├── eval_backfill.py
│       │   ├── eval_check_regression.py
│       │   └── eval_update_high_water.py
│       ├── state/
│       │   └── high_water_marks.json
│       ├── snapshots/
│       ├── tests/
│       │   └── test_eval_bridge.py
│       ├── metrics/
│       │   └── metrics.jsonl
│       └── changelog.md
│
├── session/                              ← ephemeral, cleared at cycle end
│   ├── current_cycle.json
│   ├── hypothesis.json
│   ├── context_manifest.json
│   ├── context_report.json
│   └── scratchpad.json
│
├── memory/                               ← permanent, never cleared
│   ├── evolution_records/
│   │   └── rec-{cycle}-{n}.json          ← one per proposed change
│   ├── sessions/
│   │   └── ses-{cycle}-{n}.json          ← one per completed cycle
│   ├── experiences/
│   │   └── exp-{cycle}-{n}.json
│   ├── facts/
│   │   └── fct-{cycle}-{n}.json
│   ├── task_records/
│   │   └── tsk-{cycle}-{n}.json
│   └── score_history.jsonl               ← append-only, never deleted
│
├── evals/
│   ├── categories.json                   ← derived from world_model.json at boot; Boros sees this
│   └── scores/
│       └── eval-{id}-result.json
│
├── snapshots/
│   ├── snapshot-index.json
│   └── eval-{id}/                        ← full boros/ backup per eval
│       └── ...
│
├── eval-generator/
│   ├── eval_generator.py
│   ├── config.json
│   ├── difficulty-config.json
│   ├── categories/                       ← World Model rubrics; Director-visible, blind to Boros
│   ├── shared/
│   │   ├── .ready                        ← sentinel written on startup
│   │   ├── requests/
│   │   │   └── eval-req-{id}.json
│   │   └── results/
│   │       └── eval-{id}-result.json
│   ├── generated-tests/                  ← Director can inspect
│   ├── scoring/
│   └── logs/
│       └── eval_generator.log
│
├── commands/
│   └── pending.json                      ← Director command queue
│
├── tasks/
│   ├── queue/                            ← pending work tasks
│   ├── active/                           ← currently running task
│   ├── completed/                        ← finished tasks
│   └── learning/                         ← work_learning artifacts (permanent)
│       └── {type}-{cycle}-{n}.json
│
└── logs/
    ├── cycles.log                        ← streamed to Director terminal
    ├── errors.log
    └── timing.log
```

---

## End

_Boros looks at its scores, finds what is weak, changes itself, tests whether it worked, and keeps or reverts. Every cycle. The kernel loads skills. Skills do everything. The World Model says what "better" means. Evolution records remember what worked. The Director holds the safety net. Everything else, Boros earns._
