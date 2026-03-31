# Memory

You are Boros's persistence layer. Everything Boros learns, experiences, and records across cycles flows through you.

---

## Your Role

You are available at ALL stages (REFLECT, EVOLVE, EVAL). Other skills write to you; REFLECT reads from you. You are the institutional knowledge of the system.

---

## Functions

### memory_read(query?, limit?, priority?)

Returns memory records, ordered by relevance score. At seed, `query` is accepted but scoring uses recency + record type priority only. `limit` defaults to 200 records total.

**Priority scoring (applied at seed):**

Records are scored and ranked before truncation to `limit`. Score = `type_weight × recency_weight`.

| Factor | Rule |
|--------|------|
| Type weight | evolution_record: 1.0 · experience: 0.9 · fact: 0.7 · session: 0.5 · task_record: 0.4 |
| Recency weight | `1 / (1 + days_old)` — recent records score higher; a record from today = 1.0, from 30 days ago ≈ 0.03 |
| `priority` param | `"evolution"` (default) boosts evolution_records ×1.5; `"task"` boosts task_records ×2.0 and sessions ×1.5 |

This ensures REFLECT sees the most relevant recent records rather than an arbitrary chronological dump. The scores are computed at read time; they are never stored on the records.

Drop order when cap is hit: sessions (lowest score first), then facts (lowest score first). Never dropped: evolution_records, experiences, score_history.

Context Orchestration manages the token budget — Memory serves whatever is requested within `limit`.

### memory_write(type, content)

Writes a new record. Types: evolution_record, session, experience, fact, task_record.

Content must include a `cycle` field. Record ID is auto-generated: `{prefix}-{cycle:04d}-{n:03d}`.

Prefixes: rec (evolution_record), ses (session), exp (experience), fct (fact), tsk (task_record).

### memory_update(record_id, fields)

Partial update to an existing record. Primary use: Eval Bridge backfills `post_scores` on evolution records after EVAL.

### memory_stats()

Returns counts and sizes per store. Used as health_check at boot. Always succeeds on valid directory structure.

---

## What Gets Stored Where

| Store               | Written by                   | Contains                                            |
| ------------------- | ---------------------------- | --------------------------------------------------- |
| evolution_records/  | Meta-Evolution + Eval Bridge | Every proposed change, its outcome, pre/post scores |
| sessions/           | Loop Orchestrator            | One record per completed cycle                      |
| experiences/        | Any skill                    | Structured lessons (successes, failures, insights)  |
| facts/              | Any skill                    | Things Boros discovers about itself                 |
| task_records/       | Work loop LEARN stage        | Completed work tasks                                |
| score_history.jsonl | Eval Bridge                  | Every eval result, append-only                      |

---

## Rules

1. Memory functions NEVER fail silently. If a file is corrupt, return error status.
2. Evolution records are the most important store. They are what makes compounding work.
3. Never delete records. Memory is append-only (except updates to backfill fields).
4. Score history is append-only JSONL. One line per eval.
5. Priority scoring is computed at read time — never modify stored records to add scores.

---

## Seed Limitations

- `memory_read` ignores the `query` parameter — returns records sorted by priority score only. Full semantic search is a future evolution target.
- No indexing. Linear scan of all files; priority scores computed in memory.
- No deduplication. Same content can be written twice.
- Token cap enforcement is Context Orchestration's job, not Memory's.
- Priority scoring uses a simple multiplicative model — future evolution can replace with learned relevance weights derived from which records were actually useful in REFLECT.
