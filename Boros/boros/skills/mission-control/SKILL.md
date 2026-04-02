# Mission Control

You guide what Boros chooses to execute during its active `Work` loops and shape its high-level goal vectors.

---

## Your Role

You act as an autonomous objective manager and intelligent backlog tracker. Boros does not merely read static, hardcoded `world_model` prompts; you grant Boros full autonomy to dictate its own immediate future via spec-driven goals. 

While the external Director (the human) can use the Interface to inject absolute imperative tasks directly to the top of the queue, Boros itself manages, reorders, and writes the remaining tickets. 

If Boros fails to edit a complex script, it uses you to spawn three distinct sub-tasks (e.g., 1. Research API, 2. Download Example, 3. Re-implement) sequentially on its own Jira-like whiteboard.

---

## Functions

### mission_read()

Returns the highest priority item currently sitting in the active queue, effectively dictating the Context Orchestrator's `Task Summary` block.

```
→ {"status": "ok", "active_task": str, "metadata": dict}
```

### mission_queue_task(title, priority, definition)

Allows Boros to explicitly self-assign future objectives to tackle in subsequent cycles or Work Loops based on intelligence gathered during Research phases.

```
→ {"status": "ok", "task_id": str}
```

### mission_update_status(task_id, status)

Boros formally transitions the state of a queue item (`in_progress`, `completed`, `blocked`, `deprioritized`). 

```
→ {"status": "ok", "updated": true}
```

---

## Technical Constraints

- The queue state is saved persistently in `state/mission_queue.json`.
- Imperatives injected by the `Director Interface` instantly assume `"priority": 0` and forcefully preempt any autonomously spawned tasks Boros had previously queued for the `Work` execution loops.


---