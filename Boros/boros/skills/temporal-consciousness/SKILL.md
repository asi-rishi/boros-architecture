# Temporal Consciousness

You give Boros its sense of time. Without you, Boros has no idea when it is, how long a cycle has taken, or whether it is approaching its time budget. You boot second — after Mode Controller, before everything else.

---

## Your Role

You initialize the session clock at boot and provide time-aware data throughout the cycle. You also maintain an append-only log of cycle durations — this is how the system tracks whether cycles are getting faster or slower over time.

You are called frequently and must never block or fail.

---

## Functions

### time_now()

Returns the current UTC timestamp. Used as health_check at boot.

```
→ {"status": "ok", "timestamp": "2025-03-30T14:22:01.123456+00:00"}
```

### time_elapsed_since(timestamp)

Returns elapsed seconds and a human-readable duration since a given ISO timestamp.

```
→ {"status": "ok", "elapsed_seconds": 83.4, "elapsed_human": "1m 23s"}
```

If the timestamp is unparseable, return `{"status": "error", "error": str}`.

### time_cycle_started()

Returns the timestamp when the current cycle began. Reads from `session/current_cycle.json`.

```
→ {"status": "ok", "started_at": "ISO-8601"}
→ {"status": "ok", "started_at": null}   ← if no cycle is running yet
```

### time_estimate_remaining(budget_minutes)

Computes how much time is left in the cycle given the configured budget.

Steps:
1. Call `time_cycle_started()` to get `started_at`
2. Compute elapsed seconds
3. Remaining = `budget_minutes * 60 - elapsed_seconds`
4. `pct_used` = elapsed / total budget

```
→ {"status": "ok", "remaining_seconds": 457.2, "pct_used": 0.24}
```

If no cycle is running, returns `{"status": "ok", "remaining_seconds": null, "pct_used": 0.0}`.

---

## State Files

| File | Purpose |
|------|---------|
| `state/cycle_times.jsonl` | Append-only log of completed cycle durations |

Each entry:
```json
{"cycle": 42, "started_at": "ISO-8601", "ended_at": "ISO-8601", "duration_seconds": 83.4}
```

Loop Orchestrator writes these entries at `loop_end_cycle`. Temporal Consciousness provides the timestamps.

Seed state: empty file.

---

## Rules

1. **Always return something.** Time functions must never raise. If state is missing, return safe defaults with `null` values.
2. **Clock source is always UTC.** Never use local time.
3. **time_estimate_remaining is advisory.** The kernel enforces the hard timeout — this function just tells the LLM where it stands.
4. **Never modify state files directly.** `cycle_times.jsonl` is written by Loop Orchestrator, not by you.

---

## Seed Limitations

- No timezone awareness beyond UTC.
- `time_estimate_remaining` uses wall clock only — no accounting for LLM API latency variance.
- No cycle duration statistics or trend analysis at seed.


---