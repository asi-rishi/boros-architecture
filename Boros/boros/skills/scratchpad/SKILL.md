# Scratchpad

You serve as the dynamic "Contextual Whiteboard" for Boros. You hold the specific metadata, multi-step chains, and structural variables that Boros must carry across recursive evolution or work cycles without losing focus.

---

## Your Role

You act directly as a bridge to `Context Orchestration`. While the actual Working Memory Core is kept incredibly minimalist and lean, you allow the LLM to write down arbitrary strings, summaries, URL targets, database keys, or file paths that are guaranteed to remain explicitly visible in its prompt for the immediate duration of its logic cycle.

Boros pins high-level summaries onto you while dynamically fetching the heavy, underlying texts using your tracked pointers natively when needed.

---

## Functions

### scratchpad_write(key, content, duration_cycles=1)

Appends or overwrites a highly specific memo block to the internal whiteboard.

```
→ {"status": "ok", "message": "Key 'X' pinned to Scratchpad for 1 cycle."}
```
*Note: Boros must intelligently compress `content` before writing; attempting to write 50,000 raw lines of JSON logs directly to the scratchpad will automatically truncate and throw a warning to preserve the LLM context bounds.*

### scratchpad_read(key=null)

A raw endpoint Boros triggers natively if `Context Orchestration` drops a specific whiteboard block due to cycle duration expiration. Reads a single key or the entire active dictionary.

```
→ {"status": "ok", "scratchpad": dict}
```

### scratchpad_clear(key=null)

Deletes an active memo pointer once the dependent logic routing resolves cleanly.

```
→ {"status": "ok", "cleared": true}
```

---

## Technical Constraints

- Because `Context Orchestration` automatically parses and concatenates the active Scratchpad block into the LLM prompt immediately following the `Latest Eval Scores`, Boros relies immensely on `scratchpad_write` to maintain coherence under massive load.
- If Boros recursively enters 20 deep `Skill Forge` tests, it uses the Scratchpad to log its ultimate original objective ("Why did I even start editing this module?") so it never hallucinates drift priorities mid-task.


---