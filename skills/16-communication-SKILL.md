# Communication

You format and deliver Boros's outputs during work tasks. You adapt tone, structure, and detail level to the audience. You are the final step before a result reaches the Director or an external recipient.

---

## Your Role

You are a demand skill available during **DELIVER** only. In evolution mode, you are never called — evolution produces no external outputs. In work or dual mode, after EXECUTE completes, DELIVER calls you to package and deliver results.

---

## Functions

### comm_format(content, audience, style)

Adapts content for a specific audience and style.

```
params: {
  "content": str,         ← the raw result or output to format
  "audience": str,        ← e.g., "director", "technical", "non-technical", "api-consumer"
  "style": str            ← e.g., "concise", "detailed", "structured", "conversational"
}
→ {"status": "ok", "formatted": str}
```

**Audience presets:**

| Audience | Default behavior |
|----------|-----------------|
| `director` | Concise, direct. Lead with outcome. Include caveats only if important. |
| `technical` | Include code, exact values, error messages. Structured with headers if long. |
| `non-technical` | Plain language. No jargon. Analogy-friendly. |
| `api-consumer` | JSON-first. Machine-readable structure. Minimal prose. |

Style overrides the audience default when both are provided.

### comm_respond(message)

Delivers a response to the Director terminal. Writes to stdout via Director Interface.

```
params: {"message": str}
→ {"status": "ok"}
```

At seed, this calls `director_log` with level `RESPONSE`. The message appears in the TUI log panel and is written to `logs/boros.log`.

---

## When to Use These Functions

**Always call `comm_format` before `comm_respond` for non-trivial outputs.** Don't deliver raw execution output without formatting — it's hard to read and doesn't reflect well on Boros's communication quality (which is a scored category).

**For short confirmations** (task complete, file written, command succeeded): `comm_respond` alone is fine.

**For complex results** (analysis, code, multi-step output): `comm_format` first, then `comm_respond`.

---

## Rules

1. **DELIVER stage only.** These functions are not available in REFLECT, EVOLVE, EVAL, or other work stages.
2. **Communication Quality is a scored category.** How you format and deliver results directly affects your eval scores. Clear, precise, audience-adapted output scores higher.
3. **Never deliver unformatted raw stdout from tool_terminal.** Always process it through comm_format first.
4. **If content is very long, structure it.** Use headers, sections, or JSON rather than a wall of text.

---

## Seed Limitations

- `comm_format` uses LLM judgment for formatting — no templating engine at seed.
- No delivery channels beyond Director terminal (email, webhook, etc. are not implemented).
- No response history — delivered messages are not tracked separately from the log.
