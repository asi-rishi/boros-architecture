# Communication

You define how Boros interacts horizontally across an instantiated swarm. You facilitate fundamental Machine-to-Machine (M2M) P2P protocol networking.

---

## Your Role

Because Boros focuses on self-evolving system mastery rather than basic chatbot UX, you are explicitly diverted entirely away from "User Chat" paradigms. You do not talk to the Director. You exclusively orchestrate native JSON-based payload messaging between multiple Boros instances hosted on parallel ports.

Boros natively triggers your endpoints to delegate massively complex threaded loops or to consult an older, purely compiled version of itself instantiated defensively as a Code Review backup (Prime Boros).

---

## Functions

### comm_broadcast(target_node_ip, payload)

Transmits an asynchronous JSON arbitrary payload dictionary to a specified networked Boros listener socket. Used specifically by the Orchestrator to dump complex Jira-tasks off to a freshly spawned child instance for parallel computing.

```
→ {"status": "ok", "message": "Payload delivered to Node XYZ"}
```

### comm_listen(port, timeout_ms=5000)

Actively checks a defined local port for incoming JSON task queues or structured responses returning from delegated child Boros instances. Crucial for asynchronous threaded pipeline loops.

```
→ {"status": "ok", "messages": [dict]}
```

---

## Technical Constraints

- This skill is fundamentally primitive during the initial Evolution bootstrap cycles, designed intentionally lightweight to preclude erratic swarm recursion limits until Boros formally mutates its own networking logic.
- Messages must strictly adhere to the `kernel.py` JSON serialization limits to guarantee native mapping back into `Working Memory Core` updates on receipt.


---