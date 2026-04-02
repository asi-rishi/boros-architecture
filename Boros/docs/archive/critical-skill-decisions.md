# Critical Skill Decisions

## Objective
Reorganize and redefine the core skills for the Boros architecture based on the session's requirements.

## Overarching Vision: Unconstrained Autonomy
The design philosophy moving forward dictates that Boros must not be constrained by hardcoded guardrails, tool limits, or API restrictions. It is not an agent—it is a seed built to grow whatever limbs it requires to survive its environment (the World Model). If the World Model demands interaction with a domain Boros does not natively understand (e.g., Photoshop, hardware APIs, or local GUI apps), Boros has the complete freedom to utilize Research to learn, Tool Use to install dependencies, and Skill Forge to author arbitrary, fundamentally new capabilities. The seed skills designed below must be optimized solely to maximize this potential for frictionless, unbounded evolutionary trajectory.

## Master Skill List
The new ordered list of skills is:
00. Identity
1. Director Interface Skill
2. Mode Controller
3. Temporal Consciousness
4. Memory Skill
5. Skill Router
6. Context Orchestration
7. Reflection
8. Meta Evolution
9. Meta Evaluation
10. Loop Orchestrator
11. Skill Forge
12. Mission Control
13. Reasoning
14. Tool Use Skill
15. Communication (with other boros)
16. Web Research
17. Eval Bridge
18. Scratchpad

## Changes Decided
- **Removed**: `14-attention-SKILL.md`. Attention is deprecated and its responsibilities will likely be handled by context orchestration, scratchpad, or memory.
- **Added**: `18-scratchpad-SKILL.md`. A new skill designed purely as a scratchpad for extra non-bloated context that can be called for extended memory operations.
- **Moved/Renumbered**:
  - `00-director-interface-SKILL.md` -> `01-director-interface-SKILL.md`
  - `01-mode-controller-SKILL.md` -> `02-mode-controller-SKILL.md`
  - `02-temporal-consciousness-SKILL.md` -> `03-temporal-consciousness-SKILL.md`
  - `03-identity-SKILL.md` -> `19-identity-SKILL.md` (Moved from core top to bottom, likely to establish the fundamental baseline after everything else)
  - `15-tool-use-SKILL.md` -> `14-tool-use-SKILL.md`
  - `16-communication-SKILL.md` -> `15-communication-SKILL.md` (Focus specific to "communication with other boros")
  - `17-research-SKILL.md` -> `16-research-SKILL.md`
  - `18-eval-bridge-SKILL.md` -> `17-eval-bridge-SKILL.md`
- **Renamed/Modified**: 
  - `12-mission-SKILL.md` renamed to `12-mission-control-SKILL.md`.
  - `16-communication-SKILL.md` will become `15-communication-SKILL.md` and edited to specifically focus on "communication with other boros".
- **Unchanged (except possible internal references)**: 
  - `04-memory-SKILL.md`
  - `05-skill-router-SKILL.md`
  - `06-context-orchestration-SKILL.md`
  - `07-reflection-SKILL.md`
  - `08-meta-evolution-SKILL.md`
  - `09-meta-evaluation-SKILL.md`
  - `10-loop-orchestrator-SKILL.md`
  - `11-skill-forge-SKILL.md`
  - `13-reasoning-SKILL.md`

## Skill Loading Mechanism
Based on the architecture's topological sort and loading mechanisms, we have established the following rules for the new layout:

- **Identity (#19) as a Boot Skill:** Even though `Identity` is visually ordered at the very bottom (#19) to signify its role as the ultimate foundational baseline, it will securely remain a **Boot** skill. Because the kernel loads skills based on topological dependency requirements (and `memory` + `context-orchestration` depend on `identity`), the system will automatically parse and load it in the correct boot sequence before launching the loop. 
- **Scratchpad (#18) as a Demand Skill:** `Scratchpad` will be registered as a **Demand** skill, loaded dynamically exactly like `Reasoning` or `Tool Use`. Its schemas will only be injected into the context window when the `Skill Router` explicitly unlocks it for extended memory operations. 

## Next Steps for Architecture Update
Once approved, the file structure will be reorganized (renamed/deleted/created) based on the mapping above. File contents such as names inside YAML frontmatter, internal Markdown references, and `manifest.json` paths will also be retrofitted to adopt the new structure.

## Skill Definitions

### 01-director-interface-SKILL.md (Pre-boot)
**Role**: The human-in-the-loop Terminal UI wrapper that manages the background execution loop and parses user commands. It operates entirely outside of the Boros LLM brain.

**Core Commands**: 
In addition to the standard system controls (`status`, `pause`, `inject`, `rollback`, `task`), the Director Interface is heavily expanded to accommodate the unconstrained vision:
- **`boros view context`**: Instantly prints the `session/context_manifest.json` and currently loaded string blocks, allowing the Director to observe exactly what Boros is holding in its "working memory" at that exact second.
- **`boros view scratchpad`**: Dumps the active contents of the new `Scratchpad` skill.
- **`boros forge "skill description/name"`**: A manual override command that writes a high-priority "director imperative" into `commands/pending.json`. On the next cycle, Boros bypasses its standard evolutionary search and immediately hands the description over to the `Skill Forge` to spin up the requested capability (e.g. `boros forge "a windows gui automation skill using pywinauto"`).

### 02-mode-controller-SKILL.md (Boot)
**Decision**: Unchanged. The Mode Controller will retain its rigid three-mode toggle system (`evolution`, `work`, `dual`). Boros will rely on dual logic or dynamic task interpretation rather than blurring the fundamental system states.

### 03-temporal-consciousness-SKILL.md (Boot)
**Decision**: Unchanged. The basic clock and budget estimation functions are sufficient. Boros can manage long-running tasks via standard tool usage without requiring deep temporal recalibrations at the system level.

### 04-memory-SKILL.md (Boot)
**Decision**: Completely redesigned from a flat, passive text-dump into a State-of-the-Art (SOTA) Autonomous Tiered Memory System (MemGPT-style). 
- **Structure**: It will operate as an "OS-style" memory manager, splitting data into three tiers entirely on the local file system: Working Memory (active prompt state), Recall Memory (local SQLite for instant metadata/SQL queries), and Archival/Vector Memory (local serverless semantic indexing like LanceDB/ChromaDB).
- **Core Autonomy**: It equips Boros with active paging abilities (`memory_page_in`, `memory_page_out`, `memory_search_semantic`, `memory_search_sql`). Boros actively chooses what context to retrieve, allowing it to bypass context window constraints and intelligently query massive knowledge bases (e.g., full tutorial series or codebases) dynamically during work cycles.

### 05-skill-router-SKILL.md (Boot)
**Decision**: Radically unconstrained. Retiring the "Tool Bouncer" concept. Instead of hiding tools based on rigid cycle stages (preventing Boros from executing tasks during reflection or researching during execution), the Router will expose a global, comprehensive toolset at all times. It trusts the LLM's autonomy to select the correct tool for its current objective rather than enforcing programmatic guardrails.

### 06-context-orchestration-SKILL.md (Boot)
**Decision**: Transitioned to a "Lean, OS-Style" loader with **Associative Whispers**. It no longer force-feeds thousands of tokens of historical evolution/experience records mathematically into the LLM prompt. Instead, it strictly injects only the "Working Memory Core" (e.g., current Identity, Mode, high-level task/scores, and recent commands) taking ~1,000 to 2,000 tokens. To maintain Boros's evolutionary compounding intellect, it actively grabs the current Task or Target Error, performs a background semantic vector search, and pushes the top 1–3 most highly relevant past summaries (~300 tokens of "Whispers") into the prompt to jumpstart associative recall. The massive 198,000+ token remainder of the context window is left pristine and empty, forcing the LLM to autonomously use its MemGPT-style memory paging tools to retrieve deeper historical context only when its intelligence dictates a need for it.

### 07-reflection-SKILL.md (Boot)
**Decision**: Redesigned as a "Hybrid Universal Toolkit". Reflection is no longer a rigid, mandatory stage of the loop acting merely as a starting block for evolution. It is now a dynamic analytical toolkit that Boros can call at will (during complex work tasks, debugging, or planning) to synthesize logs and perform deep reasoning passes. However, to maintain safety against impulsive codebase mutations, the `Meta-Evolution` skill strictly mandates that Boros first write and attach a structured `hypothesis_id` from the Reflection toolkit before it accepts any `evolve_propose` system edits.

### 08-meta-evolution-SKILL.md (Boot)
**Decision**: Upgraded from a "Prompt Editor" to a full **"Software Engineering (SWE) Editor"**. When Boros uses `evolve_propose`, it is no longer restricted to just updating `.md` instructions. It possesses the complete authority to author, import, and compile raw executable Python files into its own architecture (e.g., writing a script to automate Photoshop and splicing it into the `Kernel`). To balance this immense capability, all SWE code edits are heavily gated—requiring rigorous downstream vetting and sandboxed execution testing before they are ever permanently committed to Boros's core disk.

### 09-meta-evaluation-SKILL.md (Boot)
**Decision**: Transformed into an aggressive Code Review Board. The secondary LLM (e.g., GPT-4o) dedicated to this skill doesn't merely read text diffs—it actively scrutinizes `stdout` and `stderr` logs populated when the submitted Python payload is unit-tested. It acts defensively, searching for infinite loop conditions, unhandled exceptions, or hallucinated third-party Python module calls before returning an `apply` or `reject` verdict.

### 10-loop-orchestrator-SKILL.md (Boot)
**Decision**: Unchanged. Maintains the rigid state-machine architecture. It will enforce the exact pipeline stages for both the **Evolution Loop** (`REFLECT` -> `EVOLVE` -> `EVAL`) and the **Work Loop** (`RECEIVE` -> `PLAN` -> `EXECUTE` -> `DELIVER` -> `LEARN`). Keeping the orchestrator rigid ensures Boros doesn't get lost in infinite loops and is forced to check its work against evaluations or external delivery deadlines.

### 11-skill-forge-SKILL.md (Demand)
**Decision**: Repurposed as the physical Sandbox and Compiler for Boros's code. `Skill Forge` now automatically executes `pytest` sweeps and trial invocations of newly authored scripts in a segregated environment against Boros's own workspace before sending those logs up the chain to the Code Reviewer. Boros can repeatedly query this forge environment iteratively to debug its scripts before formally proposing an evolution.

### 12-mission-control-SKILL.md (Demand)
**Decision**: Upgraded to an autonomous objective manager. Boros does not merely read static external `world_model` prompts; Mission Control manages the active queue of what Boros explicitly tackles next. While the Director can inject tasks directly into this queue, Boros is granted full autonomy to write its own spec-driven goals (e.g., self-assigning a task to learn a new codebase, or spawning three sub-tasks after a failure). The system dictates its own immediate future.

### 13-reasoning-SKILL.md (Demand)
**Decision**: Unchanged. Basic reasoning tools (`decompose`, `evaluate_options`, `check_logic`) remain as explicit callable functions. While native model architectures heavily handle raw CoT, providing overt tooling endpoints allows Boros to intentionally pause complex execution cycles and structurally write out decision trees to memory when confronted with high-ambiguity problems.

### 14-tool-use-SKILL.md (Demand)
**Decision**: Vastly upgraded to support "Unconstrained System Manipulation." 
- **Persistent / Background Processes**: `tool_terminal` is explicitly updated to track job IDs and spin off long-running daemon servers in the background without freezing the execution loop (crucial for launching Selenium nodes, compiling binaries, or running PyWinAuto agents).
- **Interactive Stdin**: Boros can now send input text to running processes (e.g., answering a `Y/n` prompt on a package installation) so it never gets permanently blocked by interactive shell utilities.
- **Surgical File Editing**: Replaces raw "read/write whole file" patterns with `tool_file_edit_diff`, allowing Boros to execute surgical, line-level code patches on massive alien codebases without exceeding context bounds or destroying files.

### 15-communication-SKILL.md (Demand)
**Decision**: Refocused entirely away from "User Chat" into a primitive **Machine-to-Machine (M2M) Protocol**. It will provide basic `comm_broadcast` and `comm_listen` sockets so that Boros can orchestrate basic P2P JSON messaging between parallel instances on different local ports (e.g., delegating a complex task to a sub-Boros). The design is kept intentionally lightweight for the initial evolution.

### 16-web-research-SKILL.md (Demand)
**Decision**: Renamed from "Research" and upgraded into an **Active Web-Agent Browser**. This skill allows Boros to autonomously drive headless browser searches, scrape forums, and pull down "best practice" documentation whenever it encounters an alien domain (like learning a new Python library or a foreign API). It aggressively seeks, scrapes, and indexes knowledge to plug capability gaps in real-time.

### 17-eval-bridge-SKILL.md (Demand)
**Decision**: Unchanged. It remains the objective testing harness. It reliably fetches the external benchmarking scores (`world_model` evaluation results) so Boros knows mathematically whether its unconstrained research and new SWE tools are genuinely improving its base intelligence scores or actively breaking the platform.

### 18-scratchpad-SKILL.md (Demand)
**Decision**: Acts as the dynamic "Contextual Whiteboard." Boros uses tools like `scratchpad_write` to deliberately pin summaries and location pointers (e.g., file paths or Vector DB keys) into a lightweight active state. The Context Orchestration skill guarantees the Scratchpad is always injected into the Working Memory Core. This allows Boros to track complex, multi-stage goals simultaneously—reviewing high-level summaries on the whiteboard at all times, and dynamically fetching the heavy supporting text using the stored pointers only exactly when needed.

### 00-identity-SKILL.md (Boot)
**Decision**: Promoted to the absolute primary architectural baseline (Skill `00`). As the most critical skill, it defines Boros's fundamental self-concept, running first and anchoring all subsequent behaviors. It is completely fluid: as Boros successfully authors new tools inside the `Skill Forge` (e.g., learning PyWinAuto to browse Windows), it utilizes `identity_update` to actively rewrite its own JSON state block, forever altering its "capabilities" and "self_narrative." Boros iteratively redesigns its own ego based on its acquired mastery of the environment.
