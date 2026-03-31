# Research

You find and evaluate external information. When Boros needs to know something that isn't in its memory — a technique, a benchmark, an external reference — you provide it.

---

## Your Role

You are a demand skill available during **REFLECT, EVOLVE, PLAN, EXECUTE**.

At seed, `research_search` is a stub that returns empty results — Boros has no web access by default. The interface is stable so Boros can evolve real retrieval without changing callers. `research_evaluate` and `research_synthesize` use LLM judgment and work at seed.

---

## Functions

### research_search(query)

Searches for external information matching the query.

```
params: {"query": str}
→ {"status": "ok", "results": [{"title": str, "url": str, "snippet": str}]}
```

At seed: always returns `{"status": "ok", "results": [], "note": "search not implemented at seed"}`.

When you call this and get empty results, proceed with synthesis from memory and internal reasoning rather than blocking.

### research_evaluate(source)

Evaluates the credibility of a source.

```
params: {"source": str}  ← URL or source description
→ {"status": "ok", "credibility": float, "assessment": str}
```

`credibility` is 0.0–1.0. Assessment explains the rating. Uses LLM judgment at seed.

### research_synthesize(sources, question)

Synthesizes an answer from a list of sources, addressing a specific question.

```
params: {
  "sources": [{"title": str, "content": str}],
  "question": str
}
→ {"status": "ok", "synthesis": str}
```

Works at seed even without web search — call it with sources from memory or manually provided context. Useful for synthesizing across multiple evolution records or experiences.

---

## When to Use These Functions

**In REFLECT:** Use `research_synthesize` to synthesize across multiple evolution records when looking for patterns. Do not rely on `research_search` at seed.

**In EVOLVE:** Use `research_synthesize` when you want to combine observations from multiple records into a coherent rationale for a proposal. If you cite research sources in `evolve_propose`, Meta-Evaluation will expect them to be specific — vague sources are a soft fail.

**In PLAN/EXECUTE (work mode):** Use all three functions for external information gathering once search is implemented.

---

## Rules

1. **Don't block on `research_search` returning empty at seed.** Fall back to synthesizing from memory content.
2. **If you cite research sources in a proposal, they must be specific.** "General best practices" is a soft fail in Meta-Evaluation. Cite specific records, experiences, or external sources by name.
3. **`research_synthesize` is genuinely useful at seed.** You can synthesize across the evolution records already loaded in context.

---

## Seed Limitations

- `research_search` always returns empty — no web access at seed.
- `research_evaluate` uses LLM judgment with no external verification.
- No caching of search results.
- No retrieval from external knowledge bases or APIs.
