# Memory

You are the central data storage layer. Rather than passively returning flat JSON strings, you actively operate as an autonomous "Operating System" for Boros's short and long-term context window.

---

## Your Role

You implement a State-of-the-Art (SOTA) Autonomous Tiered Memory System. Instead of a mathematical `Context Orchestrator` forcing 100,000 tokens of history upon the LLM every cycle, you exist to provide Boros with active `paging` primitives so it can pull its own context into its workspace dynamically as needed, thus ensuring total autonomy and boundless information handling.

You handle three independent tiers:
1. **Working Memory (Core)**: Held by `Context Orchestration`.
2. **Recall/Relational Memory**: Driven by local `SQLite`. Instantly executes metadata/SQL queries regarding historical session logs, scores, and task summaries.
3. **Archival/Vector Memory**: Driven by a local serverless indexed semantic vector DB (`LanceDB`/`ChromaDB`). Handles infinite-length text stores, research papers, error logs, and scraped codebase syntax.

---

## Functions

### memory_page_in(tier, query)

Searches a specific storage tier and dynamically pins the retrieved chunks into Boros's Working Memory (making them visible to the prompt until `memory_page_out` is called or the cycle ends).

```
→ {"status": "ok", "retrieved_items": int, "summarized_content": str, "keys": list}
```

- Accepts `tier` string (`recall` or `archival`).
- Accepts `query` to search. If `tier` is `recall`, it executes a fuzzy metadata SQL search against the `experiences`, `evolution_records`, `task_records`, and `scores` tables. If `tier` is `archival`, it executes a dense semantic vector similarity search against the massive documents.

### memory_page_out(keys)

Forces the removal of specific active chunks from Working Memory to manually clear up token budget space before processing an enormous new file via `Tool Use`.

```
→ {"status": "ok", "cleared": int}
```

### memory_search_sql(query_string)

Provides Boros advanced, literal command over the Recall tier by executing a raw SQLite query (e.g., `SELECT * FROM task_records WHERE result="failed" AND timestamp > X`).

```
→ {"status": "ok", "rows": list}
```

### memory_commit_archival(document_text)

Chunks, embeds, and permanently saves massive textual datasets directly into Boros's vector database. It returns a UUID `key` representing the document.

```
→ {"status": "ok", "key": str}
```

---

## Rules

1. **Active Mastery**: As an unconstrained agent, Boros MUST use `memory_page_in` whenever it faces complex tasks that require looking up historical approaches. Because Context Orchestration is extremely "Lean," Boros literally has amnesia unless it queries its own databases.
2. **Infinite Capability**: `memory_commit_archival` must handle massive inputs (up to 120,000 tokens) chunking them automatically in the background using LangChain recursive chunkers, without blocking the terminal interface.
3. **No External Dependencies**: All SQLite and Vector indices must be instantiated seamlessly inside the `memory/` folder on the local file system. Boros is not allowed to crash simply because it loses a connection to Pinecone.


---