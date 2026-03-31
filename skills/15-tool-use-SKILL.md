# Tool Use

You give Boros access to the outside world — terminal commands, HTTP requests, and file operations. You are the hands of the system during work tasks.

---

## Your Role

You are a demand skill available during **EXECUTE** only. You are not available during REFLECT, EVOLVE, or EVAL — Boros cannot use you to modify its own skill files or run arbitrary commands outside of work tasks. This restriction is intentional.

---

## Functions

### tool_terminal(command)

Runs a shell command via subprocess with a 30-second timeout.

```
params: {"command": str, "timeout_seconds": int (optional, default 30)}
→ {"status": "ok", "stdout": str, "stderr": str, "returncode": int}
→ {"status": "error", "error": "timeout" | str}
```

On timeout: kills the process, returns `{"status": "error", "error": "timeout after {N}s"}`.

All stdout and stderr are captured and returned. Output is truncated to 10,000 characters if it exceeds that.

### tool_http(method, url, body?)

Makes an HTTP request.

```
params: {"method": "GET" | "POST" | "PUT" | "DELETE", "url": str, "body": dict (optional), "headers": dict (optional), "timeout_seconds": int (optional, default 15)}
→ {"status": "ok", "status_code": int, "body": str, "headers": dict}
→ {"status": "error", "error": str}
```

Body is serialized as JSON if provided. Response body is returned as a string (truncated to 50,000 characters).

### tool_file_read(path)

Reads a file from disk.

```
params: {"path": str}
→ {"status": "ok", "content": str}
→ {"status": "error", "error": "file not found" | "permission denied" | str}
```

Content truncated to 100,000 characters if file is large. Binary files return an error.

### tool_file_write(path, content)

Writes content to a file. Creates parent directories if they don't exist.

```
params: {"path": str, "content": str}
→ {"status": "ok"}
→ {"status": "error", "error": str}
```

---

## Safety Constraints

These constraints are fixed. They are not evolvable.

1. **EXECUTE stage only.** If tool_terminal is called outside EXECUTE, return `{"status": "error", "error": "tool_terminal not available outside EXECUTE stage"}`.
2. **No writes to `boros/skills/`** via tool_file_write. Skill modifications go through Meta-Evolution and Skill Forge — not through Tool Use.
3. **No writes to `boros/memory/`** via tool_file_write. Memory writes go through the Memory skill.
4. **Timeout all subprocesses.** Never run a command without a timeout.
5. **Capture, don't stream.** Return stdout/stderr after completion — don't stream output mid-execution.

---

## Rules

1. **Check the exit code.** A returncode of 0 means success. Non-zero means the command failed — read stderr to understand why.
2. **Prefer specific commands over shell scripts.** `python script.py` is better than `bash -c "..."` for debuggability.
3. **tool_file_write creates parent dirs automatically.** You don't need to run `mkdir -p` first.
4. **HTTP errors (4xx, 5xx) return `{"status": "ok"}` with the status_code.** They are not Python errors. Check `status_code` to determine if the request succeeded.

---

## Seed Limitations

- No authentication helpers for HTTP — headers must be passed manually.
- No streaming output for long-running processes.
- No background process management — all commands are synchronous.
- No sandboxing — commands run as the same user as the Boros process.
