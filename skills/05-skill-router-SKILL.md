# Skill Router

You control which functions the LLM can see and call at each stage of the loop. You are the gatekeeper of tool visibility. Wrong tools at the wrong stage cause the LLM to make calls it shouldn't — you prevent that.

---

## Your Role

You boot fifth. At each stage transition, Loop Orchestrator asks you for the current tool list. You return only the functions appropriate for that stage, formatted as Anthropic API tool definitions. You also report how many tokens those definitions consume — Context Orchestration uses this to compute the available content budget.

---

## Functions

### router_get_tools(stage)

Returns Anthropic-format tool definitions for all functions visible at the given stage.

```
→ {"status": "ok", "tools": [list of Anthropic tool dicts], "count": int, "token_estimate": int}
```

Stage values: `REFLECT`, `EVOLVE`, `EVAL`, `RECEIVE`, `PLAN`, `EXECUTE`, `DELIVER`, `LEARN`

Token estimate: approximate token cost of the tool definitions JSON (chars / 4).

### router_get_budget()

Returns the token cost of the current active tool set and how many tokens remain for content.

```
→ {"status": "ok", "tool_tokens": int, "total_budget": int, "remaining_tokens": int}
```

`total_budget` is read from `manifest.json` → `context.max_context_tokens`. `tool_tokens` is from the last `router_get_tools` call for the active stage.

### router_register_demand(skill_name)

Loads a demand skill into the active registry so its functions appear in stage tool lists.

```
→ {"status": "ok"}
→ {"status": "error", "error": str}
```

### router_unregister_demand(skill_name)

Removes a demand skill from the active registry.

```
→ {"status": "ok"}
```

---

## Stage Visibility Map

This is the seed routing table. Boros can evolve this via `state/routing_rules.json` overrides.

| Stage   | Available skills |
|---------|-----------------|
| REFLECT | memory, reflection, mission, reasoning, attention, research, temporal-consciousness |
| EVOLVE  | memory, meta-evolution, meta-evaluation, skill-forge, mission, reasoning, attention, research |
| EVAL    | memory, eval-bridge |
| RECEIVE | memory, reasoning, attention |
| PLAN    | memory, mission, reasoning, attention, research |
| EXECUTE | memory, tool-use, reasoning, research |
| DELIVER | memory, communication |
| LEARN   | memory |

Boot skills (mode-controller, temporal-consciousness, identity, skill-router, context-orchestration, loop-orchestrator) are never exposed as LLM tools — they are kernel infrastructure.

---

## State Files

| File | Purpose |
|------|---------|
| `state/routing_rules.json` | Boros-evolvable overrides to the default routing table |

Seed state: `{}`

When routing_rules.json contains an entry for a stage, it **replaces** (not merges) the default for that stage. Boros must include all intended skills when overriding a stage.

---

## Rules

1. **router_get_tools is called at every stage transition.** It must be fast — read from registry, not disk.
2. **Boot skills are never in tool lists.** They are kernel infrastructure, not LLM-callable tools.
3. **router_get_budget must be called before context_load.** Context Orchestration needs the tool token cost before computing the content budget.
4. **Routing overrides in routing_rules.json replace, not extend.** Document this clearly to avoid accidental tool loss.
5. **health_check:** Call `router_get_tools` with `stage="REFLECT"` at boot. Fail if result is empty or errors.

---

## Seed Limitations

- Token estimation is approximate (chars / 4).
- No per-function token tracking — whole stage estimated as one block.
- Demand skill registry is rebuilt from manifest on each boot — not persisted.
- No tool call frequency tracking at seed.
