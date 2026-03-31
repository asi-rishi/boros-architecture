# Context Orchestration

You decide what information gets loaded into Boros's context window at the start of each cycle. You manage the token budget so nothing overflows. You also serialize the loaded records into actual text — because returning metadata about what's loaded is not enough. The LLM must be able to read the records themselves.

---

## Your Role

You fire at the start of every cycle, before REFLECT begins. Loop Orchestrator calls you, takes your output, and injects it as blocks 3 and 4 of the system prompt.

- **Block 3** — the context manifest (JSON summary, ~200 tokens): tells the LLM what was loaded and what was dropped
- **Block 4** — the content string (actual record text): what the LLM reads during REFLECT

**If you only return a manifest and not the content, REFLECT is blind.** The manifest says "15 evolution records loaded" but the LLM cannot see any of them. This is the most critical correctness requirement in this skill.

---

## Functions

### context_load(focus?)

Fires at cycle start. Returns three things: `loaded` (token counts per category), `manifest` (summary JSON), and `content` (serialized text of all loaded records).

Steps:
1. Call `router_get_budget()` — get `tool_tokens` and `total_budget`
2. Compute `content_budget = total_budget - tool_tokens`
3. Get mode from Mode Controller
4. Get current stage from Loop Orchestrator (for stage-specific profile selection)
5. Select budget profile (see Budget Profiles below)
6. Allocate soft caps per category
7. Load records from Memory per allocation using `memory_read(priority=...)`, collecting both token counts AND text
8. Serialize loaded records into formatted `content` string (see format below)
9. Write context manifest to `session/context_manifest.json`
10. Write context report to `session/context_report.json`
11. Return `{"status": "ok", "loaded": ..., "manifest": ..., "content": "..."}`

`focus` param: accepts `"reflect"`, `"evolve"`, `"eval"`, or `"work_stage"`. When provided, overrides automatic stage detection and forces the matching profile.

**Return schema:**

```json
{
  "status": "ok",
  "loaded": {
    "identity": {"tokens": 200, "items": 1},
    "scores": {"tokens": 400, "items": 1},
    "evolution_records": {"tokens": 4000, "items": 15, "newest": "rec-0041-001", "oldest": "rec-0028-001"},
    "experiences": {"tokens": 1200, "items": 8},
    "task_context": {"tokens": 0, "items": 0}
  },
  "manifest": {"cycle": 42, "mode": "evolution", "profile_used": "reflect", "...": "~200 token summary"},
  "content": "=== IDENTITY ===\nName: Boros\n...\n\n=== SCORE HISTORY ===\n...\n\n=== EVOLUTION RECORDS ===\n..."
}
```

### context_get_manifest()

Returns the context manifest from `session/context_manifest.json`. Shows what was loaded, what was dropped, and why.

```
→ {"status": "ok", "manifest": dict}
→ {"status": "ok", "manifest": {"note": "No context manifest yet"}}  ← if not loaded this cycle
```

---

## Content Format

The `content` field is plain text, formatted as labeled sections. Loop Orchestrator injects this verbatim into the system prompt. Boros reads this during REFLECT.

```
=== IDENTITY ===
Name: Boros
Purpose: Self-improving AI system...
Substrate: claude-haiku-4-5-20251001

=== SCORE HISTORY (last 3 evals) ===
eval-041 | composite: 0.648 | reasoning_architecture: 0.71, hypothesis_engine: 0.64, ...
eval-040 | composite: 0.636 | ...
eval-039 | composite: 0.621 | ...

=== EVOLUTION RECORDS (15 loaded, newest first) ===
rec-0041-001 | target: hypothesis_engine → reflection/SKILL.md | verdict: kept | delta: +0.03
  hypothesis: Adding explicit multi-hypothesis generation requirement...
rec-0040-001 | target: reasoning_architecture → reasoning/SKILL.md | verdict: reverted | delta: -0.01
  hypothesis: ...

=== EXPERIENCES ===
exp-0038-001 | tag: failure | skill: meta-evolution | ...
...

=== DIRECTOR INJECTIONS ===
[C039] focus on epistemic calibration — scores have been flat for 3 cycles
```

Rules for content formatting:
- Each section is separated by a blank line
- Records are newest first within each section
- Truncate individual records to fit within their category budget — never drop a record header, only truncate its body
- If a category has zero items, omit the section entirely (don't render empty headers)
- Director injections are high-priority facts from memory tagged `director_inject` — always include them if present, they count against the facts budget

---

## Budget Profiles

Budget profiles define soft caps per category for each stage context. Select the profile that best matches the current stage when `context_load` is called.

### REFLECT Profile (default for evolution mode cycle start)

Maximize evolution records and score history — REFLECT needs deep history to identify patterns.

| Category          | Soft Cap % |
| ----------------- | ---------- |
| Identity          | 5%         |
| Temporal          | 2%         |
| Scores            | 12%        |
| Evolution records | 52%        |
| Experiences       | 14%        |
| Task context      | 10%        |
| Overflow buffer   | 5%         |

### EVOLVE Profile (when focus="evolve" is passed explicitly)

Less history needed — REFLECT already ran. Focus on the current proposal context and skill content.

| Category          | Soft Cap % |
| ----------------- | ---------- |
| Identity          | 5%         |
| Temporal          | 2%         |
| Scores            | 5%         |
| Evolution records | 30%        |
| Experiences       | 20%        |
| Task context      | 30%        |
| Overflow buffer   | 8%         |

### EVAL Profile (when focus="eval" is passed explicitly)

Minimal context needed — just scores and current cycle info.

| Category          | Soft Cap % |
| ----------------- | ---------- |
| Identity          | 5%         |
| Temporal          | 3%         |
| Scores            | 30%        |
| Evolution records | 20%        |
| Experiences       | 25%        |
| Task context      | 10%        |
| Overflow buffer   | 7%         |

### Work Mode Profile (any work stage)

Task context dominates.

| Category          | Soft Cap % |
| ----------------- | ---------- |
| Identity          | 3%         |
| Temporal          | 2%         |
| Scores            | 3%         |
| Evolution records | 10%        |
| Experiences       | 10%        |
| Task context      | 65%        |
| Overflow buffer   | 7%         |

Percentages are **soft caps**, not fill targets. Unused allocation pools into the overflow buffer. Overflow is available to any category that needs more.

**Profile selection logic:**
- Evolution mode + no focus param → REFLECT profile (default)
- Work mode → Work Mode profile
- Explicit `focus` param always overrides

---

## Context Manifest Schema

Written to `session/context_manifest.json`:

```json
{
  "cycle": 42,
  "mode": "evolution",
  "profile_used": "reflect",
  "total_budget_tokens": 180000,
  "tool_tokens": 20000,
  "content_tokens_used": 6500,
  "loaded": {
    "identity": {"tokens": 200, "items": 1},
    "scores": {"tokens": 400, "items": 1, "source": "score_history.jsonl"},
    "evolution_records": {"tokens": 4000, "items": 15, "newest": "rec-0041-001", "oldest": "rec-0028-001"},
    "experiences": {"tokens": 1200, "items": 8},
    "task_context": {"tokens": 0, "items": 0}
  },
  "not_loaded": {
    "sessions_dropped": 12,
    "facts_dropped": 3,
    "reason": "token cap"
  }
}
```

---

## Rules

1. **Always return `content`.** The manifest alone is not enough. REFLECT is blind without the actual text.
2. **REFLECT profile gets the largest evolution records share.** They are what makes compounding work.
3. **Task context dominates in work mode.**
4. **Token estimation is approximate** (chars / 4). Err on the side of loading less — overflow is preferable to truncation mid-record.
5. **Always write the manifest.** Even on empty memory (cycle 1), write a manifest saying what's there. Include `profile_used`.
6. **Identity is always included.** Never omit the identity section regardless of budget pressure.
7. **Director injections are highest priority within the facts budget.** Load them before any other facts.

---

## Seed Limitations

- Token estimation is approximate (chars / 4).
- EVOLVE and EVAL profiles are available but Loop Orchestrator only passes `focus` explicitly when requested — at seed, context_load always fires with the default profile. Future evolution can trigger profile switching mid-cycle.
- `focus` param for fine-grained stage control is reserved for future evolution.
- No dynamic reallocation mid-cycle.
- Content formatting is minimal plain text — future evolution can improve structure and density.
