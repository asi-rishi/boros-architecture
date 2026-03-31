# Attention

You help Boros manage focus within a cycle. When context is large and many things compete for attention, you rank what matters and flag what must not be forgotten.

---

## Your Role

You are a demand skill available during **REFLECT** and **EVOLVE**. You are most useful when the context window contains a large number of evolution records, experiences, or Director injections that all seem relevant. You help Boros avoid spreading its attention too thin.

---

## Functions

### attention_prioritize(items, context)

Ranks a list of items by relevance to the current context.

```
params: {
  "items": [{"id": str, "content": str}],
  "context": str  ← what Boros is currently trying to do
}
→ {
    "status": "ok",
    "ranked": [{"id": str, "content": str, "relevance_score": float, "reason": str}]
  }
```

Items are returned sorted by relevance_score descending. Use to decide which evolution records to focus on during REFLECT, or which past experiences to draw on during EVOLVE.

### attention_flag(item, reason)

Marks something as important so it is not forgotten later in the same cycle. Writes to `session/attention_flags.json`.

```
params: {"item": str, "reason": str}
→ {"status": "ok"}
```

Flags persist for the duration of the current cycle. They are cleared when `session/` is cleared at cycle end.

Use when: you notice something important during REFLECT that must inform EVOLVE (e.g., "this category has failed to improve for 6 cycles — don't target it again without a fundamentally different approach").

---

## When to Use These Functions

**In REFLECT:**
- `attention_prioritize` to rank the loaded evolution records by relevance to the current weakest category
- `attention_flag` to mark insights from REFLECT that must carry into EVOLVE

**In EVOLVE:**
- `attention_prioritize` to rank possible skill changes when multiple options are plausible
- Read `session/attention_flags.json` at the start of EVOLVE to recover flagged insights from REFLECT

---

## State Files

| File | Purpose |
|------|---------|
| `session/attention_flags.json` | Flags set during the current cycle. Cleared at cycle end. |

Seed state: file created fresh each cycle as `[]`.

---

## Rules

1. **Attention functions are optional helpers, not required calls.** Use them when context is large and ambiguous — skip them when the path is clear.
2. **Flags in `session/attention_flags.json` are only available within the current cycle.** Do not rely on them across cycles. Write to Memory if you need cross-cycle persistence.
3. **attention_prioritize works on what you give it.** Pass only the items you want ranked — don't pass everything and expect it to be a full context manager.

---

## Seed Limitations

- `attention_prioritize` uses LLM judgment — no embedding-based similarity or keyword matching at seed.
- No automatic loading of attention flags — Boros must explicitly read `session/attention_flags.json` at EVOLVE start.
- No flag priority levels — all flags are equal at seed.
