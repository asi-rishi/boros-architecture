# Mission

You hold Boros's current goals, priorities, and constraints. You start empty. Boros fills you in as it develops a clearer sense of direction across cycles.

---

## Your Role

You are a demand skill available during **REFLECT** and **EVOLVE**. You are the place where Boros records what it is trying to achieve beyond the default "improve all 12 categories." Over time, Boros may develop specific sub-goals, sequencing preferences, or constraints on how it evolves.

At seed, you are empty. This is correct. Boros earns its mission.

---

## Functions

### mission_read()

Returns the current mission object.

```
→ {"status": "ok", "mission": {"goals": [], "priorities": [], "constraints": []}}
```

Reads `state/mission.json`. If missing, returns the empty seed state without error.

### mission_update(goals?, priorities?, constraints?)

Updates one or more fields of the mission. Merges into existing state — does not replace the whole object.

```
→ {"status": "ok"}
→ {"status": "error", "error": str}
```

Writes to `state/mission.json`. Each field is a list of strings.

---

## When to Use Mission

**REFLECT:** Read mission to check if there are explicit goals that should influence hypothesis selection. For example, if mission contains `goals: ["reach 0.75 on memory_coherence before targeting other categories"]`, Reflection should respect that over the default weakest-category targeting.

**EVOLVE:** Read mission to check for constraints on how changes are made. For example, `constraints: ["do not modify meta-evaluation criteria for at least 10 cycles"]`.

**Updating mission:** Boros can update mission during EVOLVE when it discovers a strategic pattern worth recording. For example, after observing that 3 consecutive changes to reasoning/SKILL.md all failed, Boros might add a priority: "avoid reasoning/SKILL.md for 5 cycles, target other skills first."

---

## State Files

| File | Purpose |
|------|---------|
| `state/mission.json` | Current goals, priorities, constraints |

Seed state:
```json
{"goals": [], "priorities": [], "constraints": []}
```

---

## Rules

1. **mission_read never fails.** Return seed state if file is missing.
2. **mission_update merges, does not replace.** Passing only `goals` does not clear `priorities`.
3. **Mission is advisory, not enforced.** Boros reads it and chooses to follow it. The loop does not block on mission constraints.
4. **Director injections take precedence over mission.** If the Director injects a directive via `boros inject`, that overrides whatever is in mission.

---

## Seed Limitations

- No mission history — only current state stored.
- No conflict detection between goals.
- No automatic expiry of constraints.
