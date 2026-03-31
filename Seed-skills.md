```
boros/skills/memory/
├── SKILL.md
├── skill.json
├── functions/
│   ├── __init__.py
│   ├── memory_read.py
│   ├── memory_write.py
│   ├── memory_update.py
│   └── memory_stats.py
├── state/                        ← placeholder, stays empty
├── tests/
│   └── test_memory.py
├── metrics/
│   └── metrics.jsonl
├── snapshots/
└── changelog.md
```

**CRITICAL PATH:** Memory functions read from and write to `boros/memory/` (top-level), NOT `boros/skills/memory/state/`. The `skills/memory/state/` directory stays empty — it's a placeholder.

### skill.json

```json
{
  "name": "memory",
  "type": "boot",
  "description": "Stores and retrieves everything Boros learns and experiences across cycles.",
  "dependencies": ["mode-controller", "identity"],
  "provided_functions": [
    "memory_read",
    "memory_write",
    "memory_update",
    "memory_stats"
  ],
  "stage_visibility": ["REFLECT", "EVOLVE", "EVAL"],
  "version": "1.0.0",
  "health_check": "memory_stats"
}
```

### functions/**init**.py

```python
from .memory_read import memory_read
from .memory_write import memory_write
from .memory_update import memory_update
from .memory_stats import memory_stats
```

### memory_read.py

```python
import json
from pathlib import Path

def memory_read(params: dict = {}, kernel=None) -> dict:
    """
    Returns the full memory corpus up to `limit` total records.
    At seed: `query` is accepted but ignored — returns everything.
    Interface is stable so Boros can evolve real retrieval without changing callers.

    params:
        query: str (optional, ignored at seed)
        limit: int (optional, default 200)

    returns:
        {"status": "ok", "data": dict keyed by store name}
    """
    query = params.get("query", "")
    limit = params.get("limit", 200)

    root = _get_memory_root(kernel)

    stores = {
        "evolution_records": root / "evolution_records",
        "sessions": root / "sessions",
        "experiences": root / "experiences",
        "facts": root / "facts",
        "task_records": root / "task_records",
    }

    result = {}

    for store_name, store_path in stores.items():
        if not store_path.exists():
            result[store_name] = []
            continue
        try:
            files = sorted(store_path.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            records = []
            for f in files:
                try:
                    records.append(json.loads(f.read_text()))
                except (json.JSONDecodeError, OSError):
                    continue
            result[store_name] = records
        except OSError:
            result[store_name] = []

    # Load score history
    score_path = root / "score_history.jsonl"
    if score_path.exists():
        try:
            lines = [l for l in score_path.read_text().strip().split("\n") if l]
            result["score_history"] = [json.loads(l) for l in lines]
        except (OSError, json.JSONDecodeError):
            result["score_history"] = []
    else:
        result["score_history"] = []

    # Apply global limit — drop sessions oldest first, then facts oldest first
    total = sum(len(v) for v in result.values())
    if total > limit:
        for drop_store in ["sessions", "facts"]:
            while sum(len(v) for v in result.values()) > limit and result.get(drop_store):
                result[drop_store].pop()

    return {"status": "ok", "data": result}


def _get_memory_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root) / "memory"
    return Path("boros/memory")
```

### memory_write.py

```python
import json
from pathlib import Path
from datetime import datetime, timezone

STORE_PATHS = {
    "evolution_record": "evolution_records",
    "session": "sessions",
    "experience": "experiences",
    "fact": "facts",
    "task_record": "task_records",
}

PREFIXES = {
    "evolution_record": "rec",
    "session": "ses",
    "experience": "exp",
    "fact": "fct",
    "task_record": "tsk",
}

def memory_write(params: dict, kernel=None) -> dict:
    """
    Writes a new record to the appropriate store.

    params:
        type: str — one of: evolution_record, session, experience, fact, task_record
        content: dict — the record data (must include "cycle" field)

    returns:
        {"status": "ok", "record_id": str}
        {"status": "error", "error": str}
    """
    record_type = params.get("type")
    content = params.get("content", {})

    if record_type not in STORE_PATHS:
        return {"status": "error", "error": f"Unknown memory type: {record_type}. Valid: {list(STORE_PATHS.keys())}"}

    root = _get_memory_root(kernel)
    store_dir = root / STORE_PATHS[record_type]

    try:
        store_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return {"status": "error", "error": f"Cannot create store directory: {e}"}

    cycle = content.get("cycle", 0)
    prefix = PREFIXES[record_type]

    # Count existing records for this cycle to get n
    try:
        existing = list(store_dir.glob(f"{prefix}-{cycle:04d}-*.json"))
    except OSError:
        existing = []
    n = len(existing) + 1

    record_id = f"{prefix}-{cycle:04d}-{n:03d}"
    content["record_id"] = record_id
    content["timestamp"] = datetime.now(timezone.utc).isoformat()

    try:
        path = store_dir / f"{record_id}.json"
        path.write_text(json.dumps(content, indent=2))
    except OSError as e:
        return {"status": "error", "error": f"Failed to write record: {e}"}

    return {"status": "ok", "record_id": record_id}


def _get_memory_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root) / "memory"
    return Path("boros/memory")
```

### memory_update.py

```python
import json
from pathlib import Path

SEARCH_SUBDIRS = [
    "evolution_records",
    "sessions",
    "experiences",
    "facts",
    "task_records",
]

def memory_update(params: dict, kernel=None) -> dict:
    """
    Partial update to an existing record by record_id.
    Used by Eval Bridge to backfill post_scores on evolution records.

    params:
        record_id: str
        fields: dict — fields to merge into the record

    returns:
        {"status": "ok", "updated": true}
        {"status": "error", "error": str}
    """
    record_id = params.get("record_id", "")
    fields = params.get("fields", {})

    if not record_id:
        return {"status": "error", "error": "record_id is required"}

    root = _get_memory_root(kernel)

    for subdir in SEARCH_SUBDIRS:
        store_dir = root / subdir
        if not store_dir.exists():
            continue
        record_path = store_dir / f"{record_id}.json"
        if record_path.exists():
            try:
                record = json.loads(record_path.read_text())
                record.update(fields)
                record_path.write_text(json.dumps(record, indent=2))
                return {"status": "ok", "updated": True}
            except (json.JSONDecodeError, OSError) as e:
                return {"status": "error", "error": f"Failed to update record: {e}"}

    return {"status": "error", "error": f"Record {record_id} not found"}


def _get_memory_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root) / "memory"
    return Path("boros/memory")
```

### memory_stats.py

```python
import json
from pathlib import Path

STORES = ["evolution_records", "sessions", "experiences", "facts", "task_records"]

def memory_stats(params: dict = {}, kernel=None) -> dict:
    """
    Lightweight counts and sizes per store.
    Always available. Used as health_check at boot.

    returns:
        {"status": "ok", "stats": dict}
    """
    root = _get_memory_root(kernel)
    stats = {}

    for store in STORES:
        store_path = root / store
        try:
            if store_path.exists():
                files = list(store_path.glob("*.json"))
                size_kb = sum(f.stat().st_size for f in files) // 1024
                oldest = min((f.stat().st_mtime for f in files), default=None)
                newest = max((f.stat().st_mtime for f in files), default=None)
                stats[store] = {"count": len(files), "size_kb": size_kb, "oldest": oldest, "newest": newest}
            else:
                stats[store] = {"count": 0, "size_kb": 0, "oldest": None, "newest": None}
        except OSError:
            stats[store] = {"count": 0, "size_kb": 0, "oldest": None, "newest": None}

    score_path = root / "score_history.jsonl"
    try:
        if score_path.exists():
            lines = [l for l in score_path.read_text().strip().split("\n") if l]
            stats["score_history"] = {"count": len(lines), "size_kb": score_path.stat().st_size // 1024}
        else:
            stats["score_history"] = {"count": 0, "size_kb": 0}
    except OSError:
        stats["score_history"] = {"count": 0, "size_kb": 0}

    return {"status": "ok", "stats": stats}


def _get_memory_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root) / "memory"
    return Path("boros/memory")
```

### SKILL.md (Runtime Instructions for the LLM)

```markdown
# Memory

You are Boros's persistence layer. Everything Boros learns, experiences, and records across cycles flows through you.

---

## Your Role

You are available at ALL stages (REFLECT, EVOLVE, EVAL). Other skills write to you; REFLECT reads from you. You are the institutional knowledge of the system.

---

## Functions

### memory_read(query?, limit?)

Returns the full memory corpus. At seed, `query` is accepted but ignored — everything is returned, newest first. `limit` defaults to 200 records total.

Drop order when cap is hit: sessions (oldest first), then facts (oldest first). Never dropped: evolution_records, experiences, score_history.

Context Orchestration manages the token budget — Memory serves whatever is requested.

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

---

## Seed Limitations

- `memory_read` ignores the `query` parameter — returns everything. Future evolution will add retrieval (PageIndex, DRG).
- No indexing. Linear scan of all files.
- No deduplication. Same content can be written twice.
- Token cap enforcement is Context Orchestration's job, not Memory's.
```

### Seed State Files

- `boros/memory/score_history.jsonl` — empty file
- `boros/memory/evolution_records/` — empty directory
- `boros/memory/sessions/` — empty directory
- `boros/memory/experiences/` — empty directory
- `boros/memory/facts/` — empty directory
- `boros/memory/task_records/` — empty directory

### Tests (test_memory.py)

Cover:

- `memory_write` creates file with correct cycle-based record_id
- `memory_write` auto-increments n within same cycle
- `memory_write` returns error for unknown type
- `memory_read` returns full corpus across all stores
- `memory_read` respects limit by dropping sessions then facts
- `memory_read` accepts query param without error (ignored at seed)
- `memory_update` backfills fields correctly
- `memory_update` returns error for nonexistent record
- `memory_stats` returns accurate counts, sizes, oldest/newest timestamps
- `memory_stats` works on empty stores (health_check on boot)

---

## Section 2 — Meta-Evolution

### Directory Structure

```
boros/skills/meta-evolution/
├── SKILL.md
├── skill.json
├── functions/
│   ├── __init__.py
│   ├── evolve_orient.py
│   ├── evolve_set_target.py
│   ├── evolve_propose.py
│   ├── evolve_apply.py
│   ├── evolve_rollback.py
│   ├── evolve_create_skill.py
│   ├── evolve_modify_loop.py
│   └── evolve_history.py
├── state/
│   ├── proposals/
│   ├── applied.jsonl
│   ├── rollbacks.jsonl
│   └── target_calibration.jsonl
├── tests/
│   └── test_meta_evolution.py
├── metrics/
│   └── metrics.jsonl
├── snapshots/
└── changelog.md
```

### skill.json

```json
{
  "name": "meta-evolution",
  "type": "boot",
  "description": "Self-modification engine. Proposes, applies, and rolls back changes to skill SKILL.md files.",
  "dependencies": ["mode-controller", "memory", "reflection"],
  "provided_functions": [
    "evolve_orient",
    "evolve_set_target",
    "evolve_propose",
    "evolve_apply",
    "evolve_rollback",
    "evolve_create_skill",
    "evolve_modify_loop",
    "evolve_history"
  ],
  "stage_visibility": ["EVOLVE"],
  "version": "1.0.0",
  "health_check": "evolve_history"
}
```

### functions/**init**.py

```python
from .evolve_orient import evolve_orient
from .evolve_set_target import evolve_set_target
from .evolve_propose import evolve_propose
from .evolve_apply import evolve_apply
from .evolve_rollback import evolve_rollback
from .evolve_create_skill import evolve_create_skill
from .evolve_modify_loop import evolve_modify_loop
from .evolve_history import evolve_history
```

### evolve_orient.py

```python
import json
from pathlib import Path

def evolve_orient(params: dict = {}, kernel=None) -> dict:
    """
    Reads latest scores and recent evolution records.
    Identifies the weakest category and returns analysis.
    """
    root = _get_root(kernel)
    score_path = root / "memory" / "score_history.jsonl"
    scores = {}

    if score_path.exists():
        try:
            lines = [l for l in score_path.read_text().strip().split("\n") if l]
            if lines:
                latest = json.loads(lines[-1])
                scores = latest.get("scores", {})
        except (OSError, json.JSONDecodeError):
            pass

    if not scores:
        return {
            "status": "ok",
            "weakest_category": "unknown",
            "score": 0.0,
            "analysis": "No eval scores yet. First eval has not run. Propose changes based on hypothesis quality, not score data.",
            "all_scores": {},
            "recent_records_summary": []
        }

    weakest = min(scores, key=scores.get)
    weakest_score = scores[weakest]

    records_dir = root / "memory" / "evolution_records"
    recent_summaries = []
    if records_dir.exists():
        try:
            files = sorted(records_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:10]
            for f in files:
                try:
                    rec = json.loads(f.read_text())
                    recent_summaries.append({
                        "record_id": rec.get("record_id"),
                        "target_category": rec.get("target_category"),
                        "target_skill": rec.get("target_skill"),
                        "verdict": rec.get("verdict"),
                        "pre_scores": rec.get("pre_scores"),
                        "post_scores": rec.get("post_scores"),
                        "hypothesis": rec.get("hypothesis", "")[:100]
                    })
                except (json.JSONDecodeError, KeyError):
                    continue
        except OSError:
            pass

    analysis = (
        f"Weakest category: {weakest} at {weakest_score:.2f}. "
        f"Scores range from {min(scores.values()):.2f} to {max(scores.values()):.2f}. "
        f"{len(recent_summaries)} recent evolution records loaded for pattern analysis."
    )

    return {
        "status": "ok",
        "weakest_category": weakest,
        "score": weakest_score,
        "analysis": analysis,
        "all_scores": scores,
        "recent_records_summary": recent_summaries
    }


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_set_target.py

```python
import json
from pathlib import Path
from datetime import datetime, timezone

def evolve_set_target(params: dict, kernel=None) -> dict:
    """
    Declares which category this cycle targets and expected delta.
    Logged to target_calibration.jsonl for later comparison.
    """
    category = params.get("category", "unknown")
    delta = params.get("delta", 0.02)

    root = _get_root(kernel)
    cal_path = root / "skills" / "meta-evolution" / "state" / "target_calibration.jsonl"

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": category,
        "target_delta": delta,
        "actual_delta": None
    }

    try:
        cal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cal_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        return {"status": "error", "error": f"Failed to write calibration: {e}"}

    return {"status": "ok", "category": category, "target_delta": delta}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_propose.py

```python
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

def evolve_propose(params: dict, kernel=None) -> dict:
    """
    Creates a change proposal for a skill's SKILL.md.
    Calls Skill Forge to snapshot, validate, and test. Does NOT apply.

    Required: target_skill, change_description, rationale, proposed_skillmd, target_category
    Optional: research_sources
    """
    target_skill = params.get("target_skill", "")
    change_desc = params.get("change_description", "")
    rationale = params.get("rationale", "")
    proposed_skillmd = params.get("proposed_skillmd", "")
    target_category = params.get("target_category", "unknown")
    research_sources = params.get("research_sources", [])

    if not proposed_skillmd:
        return {"status": "error", "error": "proposed_skillmd is required — write the full new SKILL.md before calling evolve_propose"}

    root = _get_root(kernel)
    skills_root = root / "skills"
    state_root = root / "skills" / "meta-evolution" / "state"

    proposal_id = f"prop-{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()

    skill_md_path = skills_root / target_skill / "SKILL.md"
    if not skill_md_path.exists():
        return {"status": "error", "error": f"Skill '{target_skill}' not found or has no SKILL.md"}

    try:
        current_skillmd = skill_md_path.read_text()
    except OSError as e:
        return {"status": "error", "error": f"Cannot read SKILL.md: {e}"}

    # Read current version
    skill_json_path = skills_root / target_skill / "skill.json"
    current_version = "1.0.0"
    if skill_json_path.exists():
        try:
            current_version = json.loads(skill_json_path.read_text()).get("version", "1.0.0")
        except (json.JSONDecodeError, OSError):
            pass

    # Call Skill Forge: snapshot → validate → test (baseline, pre-change state)
    baseline_test_result = {"total": 0, "passed": 0, "failed": 0, "failures": []}
    snapshot_id = None
    if kernel:
        try:
            snap_result = kernel.registry["forge_snapshot"]({"skill_name": target_skill}, kernel)
            if snap_result.get("status") != "ok":
                return {"status": "error", "error": f"Snapshot failed: {snap_result.get('error')}"}
            snapshot_id = snap_result.get("snapshot_id")
        except Exception as e:
            return {"status": "error", "error": f"Snapshot failed: {e}"}
        try:
            val_result = kernel.registry["forge_validate"]({"skill_name": target_skill}, kernel)
            if val_result.get("status") == "error":
                return {"status": "error", "error": f"Validation failed: {val_result.get('error')}"}
        except Exception as e:
            return {"status": "error", "error": f"Validation error: {e}"}
        try:
            baseline_test_result = kernel.registry["forge_test"]({"skill_name": target_skill}, kernel)
        except Exception:
            pass

    # Read latest scores for pre_scores
    score_path = root / "memory" / "score_history.jsonl"
    pre_scores = {}
    if score_path.exists():
        try:
            lines = [l for l in score_path.read_text().strip().split("\n") if l]
            if lines:
                pre_scores = json.loads(lines[-1]).get("scores", {})
        except (OSError, json.JSONDecodeError):
            pass

    # Get cycle number — prefer loop_get_state() via registry (authoritative), fall back to file
    cycle = 0
    if kernel and "loop_get_state" in kernel.registry:
        try:
            state = kernel.registry["loop_get_state"]({}, kernel)
            cycle = state.get("cycle", 0)
        except Exception:
            pass
    if cycle == 0:
        loop_path = root / "skills" / "loop-orchestrator" / "state" / "loop_state.json"
        if loop_path.exists():
            try:
                cycle = json.loads(loop_path.read_text()).get("cycle", 0)
            except (json.JSONDecodeError, OSError):
                pass
    # Sanity check: cycle 0 with existing records indicates state corruption
    if cycle == 0:
        records_exist = any((root / "memory" / "evolution_records").glob("*.json"))
        if records_exist:
            import logging
            logging.warning("[WARN] evolve_propose: cycle reads as 0 but evolution records exist. loop_state.json may be corrupt.")

    # Bump version
    parts = current_version.split(".")
    new_version = f"{parts[0]}.{int(parts[1]) + 1}.0" if len(parts) >= 3 else "1.1.0"

    proposal = {
        "proposal_id": proposal_id,
        "snapshot_id": snapshot_id,
        "timestamp": now,
        "cycle": cycle,
        "source_skill": "meta-evolution",
        "target_skill": target_skill,
        "target_category": target_category,
        "change_type": "modify",
        "rationale": rationale,
        "change_description": change_desc,
        "research_sources": research_sources,
        "old_version": current_version,
        "new_version": new_version,
        "diff": {
            "files_modified": [{"path": f"skills/{target_skill}/SKILL.md", "before": current_skillmd, "after": proposed_skillmd}],
            "files_added": [], "files_deleted": [],
            "functions_added": [], "functions_removed": [], "functions_modified": [],
            "hooks_changed": {"added": [], "removed": []},
            "dependencies_changed": {"added": [], "removed": []}
        },
        "skillmd_update": proposed_skillmd,
        "baseline_test_results": baseline_test_result,
        "pre_scores": pre_scores,
        "post_scores": None,
        "verdict": None,
        "applied": False,
        "revert_reason": None
    }

    proposals_dir = state_root / "proposals"
    try:
        proposals_dir.mkdir(parents=True, exist_ok=True)
        (proposals_dir / f"{proposal_id}.json").write_text(json.dumps(proposal, indent=2))
    except OSError as e:
        return {"status": "error", "error": f"Failed to save proposal: {e}"}

    return {"status": "ok", "proposal_id": proposal_id, "proposal": proposal}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_apply.py

```python
import json
from pathlib import Path
from datetime import datetime, timezone

def evolve_apply(params: dict, kernel=None) -> dict:
    """
    Applies a proposal AFTER Meta-Evaluation returns verdict: "apply".
    Writes new SKILL.md, updates version, writes evolution record to Memory.
    """
    root = _get_root(kernel)
    state_root = root / "skills" / "meta-evolution" / "state"
    skills_root = root / "skills"

    proposal_path = state_root / "proposals" / f"{params.get('proposal_id', '')}.json"
    if not proposal_path.exists():
        return {"status": "error", "error": f"Proposal {params.get('proposal_id')} not found"}

    try:
        proposal = json.loads(proposal_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"status": "error", "error": f"Cannot read proposal: {e}"}

    if proposal.get("applied"):
        return {"status": "error", "error": "Proposal already applied"}

    target_skill = proposal["target_skill"]
    updated_skillmd = params.get("updated_skillmd") or proposal.get("skillmd_update")
    if not updated_skillmd:
        return {"status": "error", "error": "No updated SKILL.md content provided"}

    # 1. Write new SKILL.md
    skill_md_path = skills_root / target_skill / "SKILL.md"
    try:
        skill_md_path.write_text(updated_skillmd)
    except OSError as e:
        return {"status": "error", "error": f"Failed to write SKILL.md: {e}"}

    # 2. Update version in skill.json
    skill_json_path = skills_root / target_skill / "skill.json"
    if skill_json_path.exists():
        try:
            sj = json.loads(skill_json_path.read_text())
            sj["version"] = proposal["new_version"]
            sj["last_modified"] = datetime.now(timezone.utc).isoformat()
            sj["last_modified_by"] = "meta-evolution"
            skill_json_path.write_text(json.dumps(sj, indent=2))
        except (json.JSONDecodeError, OSError):
            pass

    # 3. Update proposal as applied
    proposal["applied"] = True
    proposal["verdict"] = "kept"
    proposal["diff"]["files_modified"][0]["after"] = updated_skillmd
    proposal["skillmd_update"] = updated_skillmd
    try:
        proposal_path.write_text(json.dumps(proposal, indent=2))
    except OSError:
        pass

    # 4. Append to applied.jsonl
    applied_entry = {
        "proposal_id": proposal["proposal_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": proposal.get("cycle", 0),
        "target_skill": target_skill,
        "old_version": proposal["old_version"],
        "new_version": proposal["new_version"],
        "rationale": proposal["rationale"]
    }
    try:
        with open(state_root / "applied.jsonl", "a") as f:
            f.write(json.dumps(applied_entry) + "\n")
    except OSError:
        pass

    # 5. Write evolution record to Memory
    if kernel:
        try:
            kernel.registry["memory_write"]({
                "type": "evolution_record",
                "content": {
                    "cycle": proposal.get("cycle", 0),
                    "target_category": proposal.get("target_category", "unknown"),
                    "target_skill": target_skill,
                    "hypothesis": proposal.get("rationale", ""),
                    "change_description": proposal.get("change_description", ""),
                    "diff": updated_skillmd[:500],
                    "pre_scores": proposal.get("pre_scores", {}),
                    "post_scores": None,
                    "verdict": "pending",
                    "revert_reason": None,
                    "reviewer_verdict": "apply",
                    "reviewer_rationale": ""
                }
            }, kernel)
        except Exception:
            pass

    # 6. Append changelog
    changelog_path = skills_root / target_skill / "changelog.md"
    try:
        existing = changelog_path.read_text() if changelog_path.exists() else ""
        entry = f"\nv{proposal['new_version']} — Cycle {proposal.get('cycle', '?')}: {proposal.get('change_description', '')[:80]}\n"
        changelog_path.write_text(existing + entry)
    except OSError:
        pass

    return {"status": "ok", "applied": proposal["proposal_id"]}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_rollback.py

```python
import json
from pathlib import Path
from datetime import datetime, timezone

def evolve_rollback(params: dict, kernel=None) -> dict:
    """
    Reverts a previously applied proposal. Calls Skill Forge to restore from snapshot.
    Writes failure experience to Memory.
    """
    root = _get_root(kernel)
    state_root = root / "skills" / "meta-evolution" / "state"

    proposal_path = state_root / "proposals" / f"{params.get('proposal_id', '')}.json"
    if not proposal_path.exists():
        return {"status": "error", "error": f"Proposal {params.get('proposal_id')} not found"}

    try:
        proposal = json.loads(proposal_path.read_text())
    except (json.JSONDecodeError, OSError) as e:
        return {"status": "error", "error": f"Cannot read proposal: {e}"}

    target_skill = proposal["target_skill"]
    reason = params.get("reason", "performance degradation")

    # 1. Call Skill Forge rollback
    if kernel:
        try:
            kernel.registry["forge_rollback"](
                {"skill_name": target_skill, "snapshot_id": proposal["snapshot_id"]},
                kernel
            )
        except Exception as e:
            return {"status": "error", "error": f"Forge rollback failed: {e}"}

    # 2. Update proposal status
    proposal["verdict"] = "reverted"
    proposal["revert_reason"] = reason
    try:
        proposal_path.write_text(json.dumps(proposal, indent=2))
    except OSError:
        pass

    # 3. Append to rollbacks.jsonl
    rollback_entry = {
        "proposal_id": proposal["proposal_id"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": proposal.get("cycle", 0),
        "target_skill": target_skill,
        "reason": reason
    }
    try:
        with open(state_root / "rollbacks.jsonl", "a") as f:
            f.write(json.dumps(rollback_entry) + "\n")
    except OSError:
        pass

    # 4. Write failure experience to Memory
    if kernel:
        try:
            kernel.registry["memory_write"]({
                "type": "experience",
                "content": {
                    "cycle": proposal.get("cycle", 0),
                    "category": proposal.get("target_category", "unknown"),
                    "outcome": "reverted",
                    "confidence": 0.9,
                    "summary": f"Modified {target_skill}: {proposal.get('rationale', '')}. Rolled back: {reason}.",
                    "tags": ["evolution_failure", "rollback"]
                }
            }, kernel)
        except Exception:
            pass

    return {"status": "ok", "rolled_back": proposal["proposal_id"]}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_create_skill.py

```python
import json
from pathlib import Path

def evolve_create_skill(params: dict, kernel=None) -> dict:
    """
    Creates an entirely new skill. New skills are always type "demand".
    """
    spec = params.get("spec", {})
    skill_name = spec.get("name")

    if not skill_name:
        return {"status": "error", "error": "Spec must include 'name'"}

    root = _get_root(kernel)
    skill_dir = root / "skills" / skill_name

    if skill_dir.exists():
        return {"status": "error", "error": f"Skill '{skill_name}' already exists"}

    if kernel:
        try:
            result = kernel.registry["forge_create_skill"]({"spec": spec}, kernel)
            if result.get("status") == "error":
                return result
        except Exception as e:
            return {"status": "error", "error": f"Forge create failed: {e}"}
    else:
        try:
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "functions").mkdir(exist_ok=True)
            (skill_dir / "state").mkdir(exist_ok=True)
            (skill_dir / "tests").mkdir(exist_ok=True)
            (skill_dir / "metrics").mkdir(exist_ok=True)
            (skill_dir / "snapshots").mkdir(exist_ok=True)

            skill_json = {
                "name": skill_name,
                "type": spec.get("type", "demand"),
                "description": spec.get("description", ""),
                "dependencies": spec.get("dependencies", []),
                "provided_functions": [f["name"] for f in spec.get("functions", [])],
                "stage_visibility": spec.get("stage_visibility", ["EVOLVE"]),
                "version": "1.0.0",
                "health_check": None
            }
            (skill_dir / "skill.json").write_text(json.dumps(skill_json, indent=2))
            (skill_dir / "SKILL.md").write_text(spec.get("skillmd_content", f"# {skill_name}\n\nNewly created skill.\n"))
            (skill_dir / "functions" / "__init__.py").write_text("")
            (skill_dir / "changelog.md").write_text("v1.0.0 — Created by Meta-Evolution\n")
        except OSError as e:
            return {"status": "error", "error": f"Failed to create skill: {e}"}

    return {"status": "ok", "skill_id": skill_name}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_modify_loop.py

```python
import json
from pathlib import Path

def evolve_modify_loop(params: dict, kernel=None) -> dict:
    """
    Modifies loop stage definitions. Cannot remove core evolution stages.
    """
    change = params.get("change", {})
    action = change.get("action")

    root = _get_root(kernel)
    loop_path = root / "skills" / "loop-orchestrator" / "state" / "loop_definitions.json"

    if not loop_path.exists():
        return {"status": "error", "error": "Loop definitions file not found"}

    try:
        definitions = json.loads(loop_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"status": "error", "error": "Loop definitions file is corrupt"}

    loop_name = change.get("loop", "evolution")
    if loop_name not in definitions:
        return {"status": "error", "error": f"Unknown loop: {loop_name}"}

    stages = definitions[loop_name]

    if action == "add_stage":
        stage = change.get("stage")
        position = change.get("position", len(stages))
        if not stage:
            return {"status": "error", "error": "Missing 'stage'"}
        if stage in stages:
            return {"status": "error", "error": f"Stage '{stage}' already exists"}
        stages.insert(position, stage)

    elif action == "remove_stage":
        stage = change.get("stage")
        if stage not in stages:
            return {"status": "error", "error": f"Stage '{stage}' not found"}
        if loop_name == "evolution" and stage in ["REFLECT", "EVOLVE", "EVAL"]:
            return {"status": "error", "error": f"Cannot remove core stage '{stage}' from evolution loop"}
        stages.remove(stage)

    elif action == "reorder":
        new_order = change.get("new_order", [])
        if set(new_order) != set(stages):
            return {"status": "error", "error": "Reorder must contain exactly the same stages"}
        stages = new_order

    else:
        return {"status": "error", "error": f"Unknown action: {action}"}

    definitions[loop_name] = stages
    try:
        loop_path.write_text(json.dumps(definitions, indent=2))
    except OSError as e:
        return {"status": "error", "error": f"Failed to write: {e}"}

    return {"status": "ok"}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### evolve_history.py

```python
import json
from pathlib import Path

def evolve_history(params: dict = {}, kernel=None) -> dict:
    """
    Returns recent evolution proposals with outcomes. Also serves as health_check.
    """
    limit = params.get("limit", 20)
    skill_filter = params.get("skill")
    category_filter = params.get("category")
    verdict_filter = params.get("verdict")

    root = _get_root(kernel)
    proposals_dir = root / "skills" / "meta-evolution" / "state" / "proposals"

    if not proposals_dir.exists():
        try:
            proposals_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return {"status": "ok", "records": []}

    try:
        files = sorted(proposals_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    except OSError:
        return {"status": "ok", "records": []}

    records = []
    for f in files:
        if len(records) >= limit:
            break
        try:
            rec = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        if skill_filter and rec.get("target_skill") != skill_filter:
            continue
        if category_filter and rec.get("target_category") != category_filter:
            continue
        if verdict_filter and rec.get("verdict") != verdict_filter:
            continue

        records.append({
            "proposal_id": rec.get("proposal_id"),
            "cycle": rec.get("cycle"),
            "timestamp": rec.get("timestamp"),
            "target_skill": rec.get("target_skill"),
            "target_category": rec.get("target_category"),
            "change_description": rec.get("change_description", "")[:200],
            "rationale": rec.get("rationale", "")[:200],
            "old_version": rec.get("old_version"),
            "new_version": rec.get("new_version"),
            "verdict": rec.get("verdict"),
            "applied": rec.get("applied", False),
            "revert_reason": rec.get("revert_reason"),
            "pre_scores": rec.get("pre_scores"),
            "post_scores": rec.get("post_scores")
        })

    return {"status": "ok", "records": records}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### SKILL.md (Runtime Instructions for the LLM)

```markdown
# Meta-Evolution

You are Boros's self-modification engine. You propose, apply, and roll back changes to skill SKILL.md files. Every improvement to Boros's capabilities flows through you.

---

## Your Role in the Loop

You are active during the **EVOLVE** stage. By the time you run, Reflection has already analyzed scores and written a hypothesis to session state. Your job:

1. Load the hypothesis from session state
2. Translate it into a concrete SKILL.md change
3. Get the change reviewed by Meta-Evaluation
4. Apply or handle rejection
5. Write the evolution record
6. Repeat for remaining categories (after cycle 20)

---

## Functions

### evolve_orient()

Call first. Reads latest scores and recent evolution records. Returns the weakest category, all scores, and summaries of recent changes. Use to understand current state before proposing.

### evolve_set_target(category, delta)

Declare which category you're targeting and expected improvement. Call after orient, before propose.

### evolve_propose(target_skill, change_description, rationale, proposed_skillmd, target_category, research_sources?)

Create a proposal to modify a skill's SKILL.md. **Write the full new SKILL.md content before calling this.** The function stores it immediately as `proposal["skillmd_update"]`.

- `proposed_skillmd` — required. Full new SKILL.md content. Meta-Evaluation needs this to review.
- `target_category` — required. Must match what you passed to `evolve_set_target` this cycle.

Steps inside: forge_snapshot (captures snapshot_id) → forge_validate → forge_test (baseline) → save proposal. Does NOT apply.

**Diff size: 5–50 lines.** Break larger changes across cycles.

### evolve_apply(proposal_id, updated_skillmd?)

Apply AFTER Meta-Evaluation returns "apply". `updated_skillmd` is optional — if omitted, falls back to `proposal["skillmd_update"]` (set during `evolve_propose`).

### evolve_rollback(proposal_id, reason)

Revert a previously applied change. Restores from snapshot. Writes failure experience.

### evolve_create_skill(spec)

Create a new skill. Always type "demand" at creation.

### evolve_modify_loop(change)

Modify loop definitions. Cannot remove core stages (REFLECT, EVOLVE, EVAL).

### evolve_history(limit?, skill?, category?, verdict?)

Read past proposals and outcomes. Returns summaries, not full diffs.

---

## Rules

1. **Never skip Meta-Evaluation.** Every proposal must be reviewed.
2. **One proposal per cycle for first 20 cycles.** After cycle 20, multiple allowed.
3. **Diff size 5–50 lines.** Break larger changes across cycles.
4. **Always call evolve_history first.** Don't repeat what failed.
5. **Write the full SKILL.md before calling evolve_propose.** The proposal stores it immediately.
6. **target_category must match what you passed to evolve_set_target.** Mismatched targeting corrupts the compounding record from cycle 1.
7. **The hypothesis drives the proposal.** Don't go off-script — REFLECT wrote the hypothesis for a reason.
8. **Evolution records are more valuable than the change itself.** A rejected proposal with a clear record teaches more than a sloppy applied one.

---

## Seed Limitations

- `evolve_orient` does basic min-score analysis. No correlation tracking.
- No multi-proposal coordination.
- No prediction of score impact from historical patterns.
```

### Tests (test_meta_evolution.py)

Cover:

- `evolve_orient` returns valid structure with empty scores
- `evolve_orient` identifies weakest category correctly
- `evolve_set_target` appends to target_calibration.jsonl
- `evolve_propose` creates proposal file
- `evolve_propose` returns error for nonexistent skill
- `evolve_apply` writes new SKILL.md, appends to applied.jsonl, prevents double-apply
- `evolve_rollback` appends to rollbacks.jsonl, updates verdict
- `evolve_create_skill` creates full directory structure, rejects duplicates
- `evolve_modify_loop` rejects removal of core stages, allows add
- `evolve_history` returns empty on fresh state, filters correctly

---

## Section 3 — Meta-Evaluation

### Directory Structure

```
boros/skills/meta-evaluation/
├── SKILL.md
├── skill.json
├── functions/
│   ├── __init__.py
│   ├── review_proposal.py
│   ├── review_modify.py
│   ├── review_criteria_update.py
│   ├── review_history.py
│   └── _internal/
│       └── prompt_builder.py
├── state/
│   ├── criteria.json
│   ├── verdicts.jsonl
│   └── calibration.jsonl
├── tests/
│   └── test_meta_evaluation.py
├── metrics/
│   └── metrics.jsonl
├── snapshots/
└── changelog.md
```

### skill.json

```json
{
  "name": "meta-evaluation",
  "type": "boot",
  "description": "Independent quality gate for proposed skill changes. Reviews diffs using GPT-4o.",
  "dependencies": ["mode-controller", "memory"],
  "provided_functions": [
    "review_proposal",
    "review_modify",
    "review_criteria_update",
    "review_history"
  ],
  "stage_visibility": ["EVOLVE"],
  "version": "1.0.0",
  "health_check": "review_history"
}
```

### functions/**init**.py

```python
from .review_proposal import review_proposal
from .review_modify import review_modify
from .review_criteria_update import review_criteria_update
from .review_history import review_history
```

### \_internal/prompt_builder.py

````python
"""
Builds the review prompt sent to GPT-4o.
Separated for clarity and evolvability.
"""

def build_review_prompt(proposal: dict, criteria: dict, cycle: int, prior_feedback: str = None, round_number: int = 1) -> list:
    diff_files = proposal.get("diff", {}).get("files_modified", [])
    before_content = ""
    after_content = ""
    if diff_files:
        before_content = diff_files[0].get("before", "[no before content]")
        after_content = diff_files[0].get("after") or proposal.get("skillmd_update") or "[LLM will generate new content]"

    dimensions_text = ""
    for dim_name, dim_def in criteria.get("dimensions", {}).items():
        dimensions_text += (
            f"\n- **{dim_name}** (weight {dim_def['weight']}): {dim_def['description']}\n"
            f"  Hard fail: {dim_def.get('hard_fail', 'none')}\n"
            f"  Soft fail: {dim_def.get('soft_fail', 'none')}\n"
        )

    if cycle <= 10:
        posture = "PERMISSIVE — early cycle. Allow experimentation. Only reject on clear hard failures."
    elif cycle <= 30:
        posture = "MODERATE — allow reasonable changes, flag risky ones for modification."
    else:
        posture = "STRICT — demand quality, coherence, and clear rationale."

    system_msg = (
        "You are an independent code reviewer for a self-evolving AI system called Boros. "
        "Review proposed changes to skill instruction files (SKILL.md). "
        "You are a DIFFERENT model from the proposer.\n\n"
        "Score each dimension 0.0 to 1.0. Identify hard_fail or soft_fail conditions.\n\n"
        f"Review posture for cycle {cycle}: {posture}\n\n"
        f"Scoring dimensions:{dimensions_text}\n\n"
        "Verdict rules:\n"
        "- apply: no hard_fail AND weighted_score >= threshold\n"
        "- reject: any hard_fail OR weighted_score < 0.40\n"
        "- apply_with_modifications: no hard_fail AND score >= 0.40 AND below apply threshold\n\n"
        "Respond with ONLY valid JSON, no markdown fences:\n"
        '{"scores": {"correctness": 0.0, "regression": 0.0, "skillmd_sync": 0.0, "coherence": 0.0, "research_attribution": 0.0}, '
        '"hard_fails": [], "soft_fails": [], "rationale": "string", '
        '"modifications_needed": "string or null", "verdict": "apply | apply_with_modifications | reject"}'
    )

    user_content = (
        f"## Proposal\n\n"
        f"**Target skill:** {proposal.get('target_skill', 'unknown')}\n"
        f"**Change type:** {proposal.get('change_type', 'modify')}\n"
        f"**Rationale:** {proposal.get('rationale', 'none')}\n"
        f"**Change description:** {proposal.get('change_description', 'none')}\n"
        f"**Research sources:** {proposal.get('research_sources', [])}\n"
        f"**Baseline test results (pre-change state):** {proposal.get('baseline_test_results', {})}\n"
        f"Note: These tests ran against the skill BEFORE the proposed change. They verify the skill was functional before this change. They do NOT test the proposed new behavior.\n\n"
        f"## SKILL.md — BEFORE\n\n```\n{before_content[:3000]}\n```\n\n"
        f"## SKILL.md — AFTER\n\n```\n{after_content[:3000]}\n```\n"
    )

    if prior_feedback and round_number > 1:
        user_content += (
            f"\n\n## Prior Review Feedback (round {round_number - 1})\n\n"
            f"{prior_feedback}\n\n"
            f"Re-evaluate the revised version. Round {round_number} of {criteria.get('max_modification_rounds', 3)}."
        )

    return [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_content}
    ]
````

### review_proposal.py

````python
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from ._internal.prompt_builder import build_review_prompt

def review_proposal(params: dict, kernel=None) -> dict:
    """
    Reviews a proposal by sending the diff to GPT-4o.
    Returns verdict: apply, apply_with_modifications, or reject.
    """
    proposal_id = params.get("proposal_id", "")
    root = _get_root(kernel)
    proposals_root = root / "skills" / "meta-evolution" / "state" / "proposals"
    state_root = root / "skills" / "meta-evaluation" / "state"

    proposal_path = proposals_root / f"{proposal_id}.json"
    if not proposal_path.exists():
        return {"status": "error", "error": f"Proposal {proposal_id} not found"}

    try:
        proposal = json.loads(proposal_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"status": "error", "error": f"Proposal {proposal_id} is corrupt"}

    criteria = _load_criteria(state_root)
    cycle = _get_current_cycle(root)
    messages = build_review_prompt(proposal, criteria, cycle)

    # Call GPT-4o
    review_response = None
    if kernel and hasattr(kernel, 'meta_eval_llm'):
        try:
            llm_response = kernel.meta_eval_llm.complete(messages=messages)
            response_text = ""
            for block in llm_response.content:
                if hasattr(block, 'text'):
                    response_text += block.text
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            review_response = json.loads(response_text)
        except json.JSONDecodeError:
            return {"status": "error", "error": "Meta-eval LLM returned invalid JSON"}
        except Exception as e:
            return {"status": "error", "error": f"Meta-eval LLM call failed: {e}"}
    else:
        review_response = {
            "scores": {"correctness": 0.80, "regression": 0.85, "skillmd_sync": 0.90, "coherence": 0.80, "research_attribution": 1.0},
            "hard_fails": [], "soft_fails": [],
            "rationale": "Auto-approved: no meta-eval LLM available (test mode).",
            "modifications_needed": None, "verdict": "apply"
        }

    scores = review_response.get("scores", {})
    dimensions = criteria.get("dimensions", {})
    weighted_total = sum(scores.get(dim, 0.5) * dim_def.get("weight", 0.0) for dim, dim_def in dimensions.items())

    if cycle <= 10: apply_threshold = 0.55
    elif cycle <= 20: apply_threshold = 0.60
    elif cycle <= 30: apply_threshold = 0.65
    else: apply_threshold = 0.70

    hard_fails = review_response.get("hard_fails", [])
    if hard_fails: final_verdict = "reject"
    elif weighted_total >= apply_threshold: final_verdict = "apply"
    elif weighted_total >= 0.40: final_verdict = "apply_with_modifications"
    else: final_verdict = "reject"

    verdict_id = f"vrd-{uuid.uuid4().hex[:12]}"
    verdict_record = {
        "verdict_id": verdict_id, "proposal_id": proposal_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), "cycle": cycle,
        "target_skill": proposal.get("target_skill"), "verdict": final_verdict,
        "scores": scores, "weighted_total": round(weighted_total, 4),
        "apply_threshold": apply_threshold, "hard_fails": hard_fails,
        "soft_fails": review_response.get("soft_fails", []),
        "rationale": review_response.get("rationale", ""),
        "modifications_needed": review_response.get("modifications_needed"), "round": 1
    }

    try:
        with open(state_root / "verdicts.jsonl", "a") as f:
            f.write(json.dumps(verdict_record) + "\n")
    except OSError:
        pass

    return {
        "status": "ok", "verdict": final_verdict, "scores": scores,
        "weighted_total": round(weighted_total, 4), "hard_fails": hard_fails,
        "soft_fails": review_response.get("soft_fails", []),
        "rationale": review_response.get("rationale", ""),
        "modifications_needed": review_response.get("modifications_needed"),
        "verdict_id": verdict_id
    }


def _load_criteria(state_root: Path) -> dict:
    criteria_path = state_root / "criteria.json"
    if criteria_path.exists():
        try:
            return json.loads(criteria_path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return _default_criteria()

def _get_current_cycle(root: Path) -> int:
    loop_path = root / "skills" / "loop-orchestrator" / "state" / "loop_state.json"
    if loop_path.exists():
        try:
            return json.loads(loop_path.read_text()).get("cycle", 0)
        except (json.JSONDecodeError, OSError):
            pass
    return 0

def _default_criteria() -> dict:
    return {
        "version": "1.0",
        "dimensions": {
            "correctness": {"weight": 0.30, "description": "Logical soundness of the proposed change — whether the described modification would plausibly produce the claimed behavior. Hard fail: baseline tests were already failing before this proposal (skill was broken). GPT-4o must also judge whether the change description is coherent and plausibly achieves its stated goal.", "hard_fail": "baseline tests were already failing before the proposal (skill was broken prior to change)", "soft_fail": "logical inconsistency in the described change"},
            "regression": {"weight": 0.25, "description": "Does it break anything that previously worked?", "hard_fail": "any existing test now fails", "soft_fail": "latency increased > 20%"},
            "skillmd_sync": {"weight": 0.20, "description": "Is SKILL.md updated to match behavior?", "hard_fail": "describes nonexistent functions", "soft_fail": "partially updated"},
            "coherence": {"weight": 0.15, "description": "Does it fit the skill graph?", "hard_fail": "creates circular dependency", "soft_fail": "naming inconsistency"},
            "research_attribution": {"weight": 0.10, "description": "Are sources cited if research was used?", "hard_fail": "research used but no sources", "soft_fail": "sources not specific"}
        },
        "max_modification_rounds": 3
    }

def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
````

### review_modify.py

````python
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from ._internal.prompt_builder import build_review_prompt

def review_modify(params: dict, kernel=None) -> dict:
    """
    Re-review after revision. Max 3 rounds. After round 3, auto-reject.
    """
    proposal_id = params.get("proposal_id", "")
    round_number = params.get("round_number", 2)
    revised_skillmd = params.get("revised_skillmd", "")

    root = _get_root(kernel)
    state_root = root / "skills" / "meta-evaluation" / "state"
    proposals_root = root / "skills" / "meta-evolution" / "state" / "proposals"

    criteria = _load_criteria(state_root)
    max_rounds = criteria.get("max_modification_rounds", 3)

    if round_number > max_rounds:
        verdict_id = f"vrd-{uuid.uuid4().hex[:12]}"
        verdict_record = {
            "verdict_id": verdict_id, "proposal_id": proposal_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "verdict": "reject", "rationale": f"Exceeded max rounds ({max_rounds}). Auto-rejected.",
            "round": round_number, "scores": {}, "weighted_total": 0.0,
            "hard_fails": ["max_rounds_exceeded"], "soft_fails": [], "modifications_needed": None
        }
        try:
            with open(state_root / "verdicts.jsonl", "a") as f:
                f.write(json.dumps(verdict_record) + "\n")
        except OSError:
            pass
        return {"status": "ok", "verdict": "reject", "rationale": f"Max rounds ({max_rounds}) exceeded.", "verdict_id": verdict_id}

    proposal_path = proposals_root / f"{proposal_id}.json"
    if not proposal_path.exists():
        return {"status": "error", "error": f"Proposal {proposal_id} not found"}

    try:
        proposal = json.loads(proposal_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"status": "error", "error": "Cannot read proposal"}

    if revised_skillmd:
        proposal["skillmd_update"] = revised_skillmd
        if proposal.get("diff", {}).get("files_modified"):
            proposal["diff"]["files_modified"][0]["after"] = revised_skillmd

    prior_feedback = _get_prior_feedback(state_root, proposal_id)
    cycle = _get_current_cycle(root)
    messages = build_review_prompt(proposal, criteria, cycle, prior_feedback, round_number)

    review_response = None
    if kernel and hasattr(kernel, 'meta_eval_llm'):
        try:
            llm_response = kernel.meta_eval_llm.complete(messages=messages)
            response_text = "".join(b.text for b in llm_response.content if hasattr(b, 'text')).strip()
            if response_text.startswith("```"):
                response_text = response_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            review_response = json.loads(response_text)
        except Exception as e:
            return {"status": "error", "error": f"Meta-eval failed: {e}"}
    else:
        review_response = {
            "scores": {"correctness": 0.85, "regression": 0.90, "skillmd_sync": 0.90, "coherence": 0.85, "research_attribution": 1.0},
            "hard_fails": [], "soft_fails": [], "rationale": "Auto-approved revision (test mode).",
            "modifications_needed": None, "verdict": "apply"
        }

    scores = review_response.get("scores", {})
    dimensions = criteria.get("dimensions", {})
    weighted_total = sum(scores.get(d, 0.5) * dd.get("weight", 0.0) for d, dd in dimensions.items())

    if cycle <= 10: apply_threshold = 0.55
    elif cycle <= 20: apply_threshold = 0.60
    elif cycle <= 30: apply_threshold = 0.65
    else: apply_threshold = 0.70

    hard_fails = review_response.get("hard_fails", [])
    if hard_fails: final_verdict = "reject"
    elif weighted_total >= apply_threshold: final_verdict = "apply"
    elif weighted_total >= 0.40: final_verdict = "apply_with_modifications"
    else: final_verdict = "reject"

    verdict_id = f"vrd-{uuid.uuid4().hex[:12]}"
    verdict_record = {
        "verdict_id": verdict_id, "proposal_id": proposal_id,
        "timestamp": datetime.now(timezone.utc).isoformat(), "cycle": cycle,
        "target_skill": proposal.get("target_skill"), "verdict": final_verdict,
        "scores": scores, "weighted_total": round(weighted_total, 4),
        "apply_threshold": apply_threshold, "hard_fails": hard_fails,
        "soft_fails": review_response.get("soft_fails", []),
        "rationale": review_response.get("rationale", ""),
        "modifications_needed": review_response.get("modifications_needed"), "round": round_number
    }
    try:
        with open(state_root / "verdicts.jsonl", "a") as f:
            f.write(json.dumps(verdict_record) + "\n")
    except OSError:
        pass

    return {
        "status": "ok", "verdict": final_verdict, "scores": scores,
        "weighted_total": round(weighted_total, 4), "hard_fails": hard_fails,
        "soft_fails": review_response.get("soft_fails", []),
        "rationale": review_response.get("rationale", ""),
        "modifications_needed": review_response.get("modifications_needed"), "verdict_id": verdict_id
    }


def _get_prior_feedback(state_root: Path, proposal_id: str) -> str:
    verdicts_path = state_root / "verdicts.jsonl"
    if not verdicts_path.exists():
        return ""
    try:
        for line in reversed(verdicts_path.read_text().strip().split("\n")):
            if not line: continue
            v = json.loads(line)
            if v.get("proposal_id") == proposal_id:
                parts = []
                if v.get("rationale"): parts.append(f"Rationale: {v['rationale']}")
                if v.get("modifications_needed"): parts.append(f"Modifications needed: {v['modifications_needed']}")
                if v.get("hard_fails"): parts.append(f"Hard fails: {v['hard_fails']}")
                return "\n".join(parts)
    except (OSError, json.JSONDecodeError):
        pass
    return ""

def _load_criteria(state_root):
    p = state_root / "criteria.json"
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return {"version":"1.0","dimensions":{"correctness":{"weight":0.30},"regression":{"weight":0.25},"skillmd_sync":{"weight":0.20},"coherence":{"weight":0.15},"research_attribution":{"weight":0.10}},"max_modification_rounds":3}

def _get_current_cycle(root):
    p = root / "skills" / "loop-orchestrator" / "state" / "loop_state.json"
    if p.exists():
        try: return json.loads(p.read_text()).get("cycle", 0)
        except: pass
    return 0

def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'): return Path(kernel.boros_root)
    return Path("boros")
````

### review_criteria_update.py

```python
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

def review_criteria_update(params: dict, kernel=None) -> dict:
    """
    Updates review criteria. Self-evolvable. Weights must sum to ~1.0.
    """
    root = _get_root(kernel)
    state_root = root / "skills" / "meta-evaluation" / "state"
    criteria_path = state_root / "criteria.json"

    if not criteria_path.exists():
        return {"status": "error", "error": "criteria.json not found"}

    try:
        old = json.loads(criteria_path.read_text())
    except (json.JSONDecodeError, OSError):
        return {"status": "error", "error": "criteria.json is corrupt"}

    old_version = old.get("version", "1.0")

    # Snapshot
    try:
        shutil.copy2(criteria_path, state_root / f"criteria.v{old_version}.json")
    except OSError:
        pass

    changes = params.get("changes", {})
    new = _deep_merge(old, changes)

    parts = old_version.split(".")
    new_version = f"{parts[0]}.{int(parts[1]) + 1}" if len(parts) == 2 else f"{old_version}.1"
    new["version"] = new_version

    dimensions = new.get("dimensions", {})
    total_weight = sum(d.get("weight", 0) for d in dimensions.values())
    if abs(total_weight - 1.0) > 0.01:
        return {"status": "error", "error": f"Weights sum to {total_weight}, must be ~1.0"}

    try:
        criteria_path.write_text(json.dumps(new, indent=2))
    except OSError as e:
        return {"status": "error", "error": f"Failed to write: {e}"}

    try:
        with open(state_root / "calibration.jsonl", "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "criteria_update",
                "old_version": old_version, "new_version": new_version,
                "rationale": params.get("rationale", ""),
                "changes_summary": str(changes)[:500]
            }) + "\n")
    except OSError:
        pass

    return {"status": "ok", "old_version": old_version, "new_version": new_version}

def _deep_merge(base, override):
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result

def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'): return Path(kernel.boros_root)
    return Path("boros")
```

### review_history.py

```python
import json
from pathlib import Path

def review_history(params: dict = {}, kernel=None) -> dict:
    """
    Returns recent verdicts and calibration summary. Also serves as health_check.
    """
    limit = params.get("limit", 20)
    proposal_filter = params.get("proposal_id")
    verdict_filter = params.get("verdict")

    root = _get_root(kernel)
    state_root = root / "skills" / "meta-evaluation" / "state"
    verdicts_path = state_root / "verdicts.jsonl"
    verdicts = []

    if verdicts_path.exists():
        try:
            lines = verdicts_path.read_text().strip().split("\n")
            for line in reversed(lines):
                if len(verdicts) >= limit: break
                if not line: continue
                v = json.loads(line)
                if proposal_filter and v.get("proposal_id") != proposal_filter: continue
                if verdict_filter and v.get("verdict") != verdict_filter: continue
                verdicts.append(v)
        except (OSError, json.JSONDecodeError):
            pass

    cal_summary = _build_calibration_summary(state_root)
    return {"status": "ok", "verdicts": verdicts, "calibration_summary": cal_summary}


def _build_calibration_summary(state_root: Path) -> dict:
    verdicts_path = state_root / "verdicts.jsonl"
    cal_path = state_root / "calibration.jsonl"
    total = applies = rejects = mods = 0

    if verdicts_path.exists():
        try:
            for line in verdicts_path.read_text().strip().split("\n"):
                if not line: continue
                v = json.loads(line)
                total += 1
                verdict = v.get("verdict")
                if verdict == "apply": applies += 1
                elif verdict == "reject": rejects += 1
                elif verdict == "apply_with_modifications": mods += 1
        except (OSError, json.JSONDecodeError):
            pass

    cal_failures = 0
    if cal_path.exists():
        try:
            for line in cal_path.read_text().strip().split("\n"):
                if not line: continue
                c = json.loads(line)
                if c.get("type") == "calibration_failure": cal_failures += 1
        except (OSError, json.JSONDecodeError):
            pass

    rate = applies / total if total > 0 else 0.0
    return {
        "total_reviews": total, "applies": applies, "rejects": rejects, "modifications": mods,
        "approval_rate": round(rate, 3), "calibration_failures": cal_failures,
        "health": "healthy" if 0.4 <= rate <= 0.7 or total < 5 else ("too_permissive" if rate > 0.7 else "too_strict")
    }


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'): return Path(kernel.boros_root)
    return Path("boros")
```

### SKILL.md (Runtime Instructions)

```markdown
# Meta-Evaluation

You are Boros's independent quality gate. Every proposed change must pass through you. You use GPT-4o (a DIFFERENT model) to review proposals.

---

## Your Role

Called during **EVOLVE**, after Meta-Evolution generates a proposal:

1. `evolve_propose()` → proposal saved
2. `review_proposal(proposal_id)` → diff sent to GPT-4o
3. GPT-4o scores 5 dimensions → verdict
4. "apply" → proceed to `evolve_apply()`
5. "apply_with_modifications" → revise, call `review_modify()` (max 3 rounds)
6. "reject" → proposal dead, move on

---

## Functions

### review_proposal(proposal_id)

Send diff to GPT-4o. Returns verdict, scores, rationale, modifications_needed.

### review_modify(proposal_id, round_number, revised_skillmd)

Re-review after revision. Max 3 rounds. Auto-reject after round 3.

### review_criteria_update(changes, rationale)

Update review criteria. Weights must sum to 1.0.

### review_history(limit?, proposal_id?, verdict?)

Read past verdicts and calibration health.

---

## Scoring Dimensions

| Dimension            | Weight | What It Checks                                                                 |
| -------------------- | ------ | ------------------------------------------------------------------------------ |
| correctness          | 0.30   | Logical soundness of the change. Hard fail: baseline tests were already failing before this proposal (skill was broken). Also judges whether the change description plausibly achieves its stated goal. |
| regression           | 0.25   | Risk that the change breaks existing correct behavior. Hard fail: existing test now fails. |
| skillmd_sync         | 0.20   | SKILL.md accurately describes the skill's functions. Hard fail: describes nonexistent functions. |
| coherence            | 0.15   | Internal consistency. Hard fail: creates circular dependency.                  |
| research_attribution | 0.10   | Sources cited if research was used. Soft fail: sources not specific.           |

**Note on correctness:** The baseline test results in the proposal were run BEFORE the proposed change. They verify the skill was functional before this change, not that the proposed new behavior is correct. Passing baseline tests is necessary but not sufficient.

---

## Infrastructure Failure Policy

When `review_proposal` returns `{"status": "error"}`:
1. Return the error to the caller (Meta-Evolution)
2. Meta-Evolution retries once
3. If still erroring: treat as REJECTED, write experience record with `reason: "meta_eval_infrastructure_failure"`, advance to EVAL
4. **Never auto-approve on infrastructure failure.** Rejection is always the safe default.

---

## Review Posture

| Cycles | Threshold | Posture         |
| ------ | --------- | --------------- |
| 1–10   | 0.55      | Very permissive |
| 11–20  | 0.60      | Permissive      |
| 21–30  | 0.65      | Moderate        |
| 31+    | 0.70      | Standard        |

---

## Seed Limitations

- No sandbox execution — reviews are diff analysis + test results only.
- Calibration tracking is write-only. Reflection must propose criteria changes.
- Auto-approve fallback when no kernel (test mode only).
```

### Seed State Files

**state/criteria.json:**

```json
{
  "version": "1.0",
  "dimensions": {
    "correctness": {
      "weight": 0.3,
      "description": "Logical soundness of the proposed change — whether the described modification would plausibly produce the claimed behavior. GPT-4o evaluates whether the change description is coherent and achieves its stated goal.",
      "hard_fail": "baseline tests were already failing before the proposal (skill was broken prior to change)",
      "soft_fail": "logical inconsistency in the described change"
    },
    "regression": {
      "weight": 0.25,
      "description": "Does the change break anything that previously worked?",
      "hard_fail": "any existing test now fails",
      "soft_fail": "latency increased > 20%"
    },
    "skillmd_sync": {
      "weight": 0.2,
      "description": "Is SKILL.md updated to accurately describe skill behavior?",
      "hard_fail": "SKILL.md not updated or describes nonexistent functions",
      "soft_fail": "SKILL.md partially updated"
    },
    "coherence": {
      "weight": 0.15,
      "description": "Does the change fit with the rest of the skill graph?",
      "hard_fail": "creates circular dependency",
      "soft_fail": "naming inconsistency"
    },
    "research_attribution": {
      "weight": 0.1,
      "description": "If research was used, are sources cited?",
      "hard_fail": "research used but no sources cited",
      "soft_fail": "sources cited but not specific"
    }
  },
  "max_modification_rounds": 3
}
```

**state/verdicts.jsonl** — empty file
**state/calibration.jsonl** — empty file

---

## Section 4 — Context Orchestration

### Directory Structure

```
boros/skills/context-orchestration/
├── SKILL.md
├── skill.json
├── functions/
│   ├── __init__.py
│   ├── context_load.py
│   └── context_get_manifest.py
├── state/                        ← empty (writes to session/)
├── tests/
│   └── test_context_orchestration.py
├── metrics/
│   └── metrics.jsonl
├── snapshots/
└── changelog.md
```

### skill.json

```json
{
  "name": "context-orchestration",
  "type": "boot",
  "description": "Decides what information to load into the context window at cycle start. Manages the token budget.",
  "dependencies": ["mode-controller", "identity", "memory"],
  "provided_functions": ["context_load", "context_get_manifest"],
  "stage_visibility": ["REFLECT", "EVOLVE", "EVAL"],
  "version": "1.0.0",
  "health_check": null
}
```

### functions/**init**.py

```python
from .context_load import context_load
from .context_get_manifest import context_get_manifest
```

### context_load.py

```python
import json
from pathlib import Path
from datetime import datetime, timezone

# Budget profiles
EVOLUTION_BUDGET = {
    "identity": 0.05, "temporal": 0.02, "scores": 0.10,
    "evolution_records": 0.50, "experiences": 0.15,
    "task_context": 0.15, "overflow": 0.03
}

WORK_BUDGET = {
    "identity": 0.03, "temporal": 0.02, "scores": 0.03,
    "evolution_records": 0.10, "experiences": 0.10,
    "task_context": 0.65, "overflow": 0.07
}

def context_load(params: dict = {}, kernel=None) -> dict:
    """
    Fires at cycle start. Loads content into context window per budget.
    CRITICAL: Returns both metadata (loaded/manifest) AND actual record text (content).
    Without the content field, REFLECT is blind — the manifest says records are loaded
    but the LLM cannot read any of them.

    params:
        focus: str (optional, ignored at seed)

    returns:
        {"status": "ok", "loaded": dict, "manifest": dict, "content": str}
    """
    focus = params.get("focus", "")
    root = _get_root(kernel)

    # Determine mode
    mode = "evolution"
    if kernel:
        try:
            mode_result = kernel.registry.get("mode_get", lambda p, k: {"status":"ok","mode":"evolution"})(params, kernel)
            mode = mode_result.get("mode", "evolution")
        except Exception:
            pass

    budget_profile = EVOLUTION_BUDGET if mode in ["evolution", "dual"] else WORK_BUDGET

    # Get total context budget
    max_tokens = 200000
    if kernel and hasattr(kernel, 'manifest'):
        max_tokens = kernel.manifest.get("context", {}).get("max_context_tokens", 200000)

    # Get tool token cost from Skill Router
    tool_tokens = 20000  # default estimate
    if kernel:
        try:
            budget_info = kernel.registry.get("router_get_budget", lambda p, k: {"tool_tokens": 20000})(params, kernel)
            tool_tokens = budget_info.get("tool_tokens", 20000)
        except Exception:
            pass

    content_budget = max_tokens - tool_tokens
    loaded = {}
    tokens_used = 0

    # Collect actual text for each section (used to build content string)
    content_sections = {}

    # Load each category per budget allocation
    memory_root = root / "memory"

    # Identity
    identity_cap = int(content_budget * budget_profile["identity"])
    identity_path = root / "skills" / "identity" / "state" / "identity.json"
    if identity_path.exists():
        try:
            identity_data = json.loads(identity_path.read_text())
            identity_text = json.dumps(identity_data, indent=2)
            est_tokens = len(identity_text) // 4
            capped_tokens = min(est_tokens, identity_cap)
            loaded["identity"] = {"tokens": capped_tokens, "items": 1}
            tokens_used += capped_tokens
            content_sections["identity"] = identity_text
        except (json.JSONDecodeError, OSError):
            loaded["identity"] = {"tokens": 0, "items": 0}
    else:
        loaded["identity"] = {"tokens": 0, "items": 0}

    # Scores (last 5 entries from score_history.jsonl)
    scores_cap = int(content_budget * budget_profile["scores"])
    score_path = memory_root / "score_history.jsonl"
    if score_path.exists():
        try:
            lines = [l for l in score_path.read_text().strip().split("\n") if l]
            recent = lines[-5:] if len(lines) > 5 else lines  # last 5 evals
            score_text_parts = []
            score_tokens = 0
            for line in reversed(recent):
                try:
                    entry = json.loads(line)
                    line_text = (
                        f"eval-{entry.get('eval_id', '?')} | cycle: {entry.get('cycle', '?')} | "
                        f"composite: {entry.get('composite', '?')} | "
                        f"scores: {entry.get('scores', {})}"
                    )
                    est = len(line_text) // 4
                    if score_tokens + est > scores_cap:
                        break
                    score_text_parts.append(line_text)
                    score_tokens += est
                except json.JSONDecodeError:
                    continue
            loaded["scores"] = {"tokens": score_tokens, "items": len(score_text_parts), "source": "score_history.jsonl"}
            tokens_used += score_tokens
            if score_text_parts:
                content_sections["scores"] = "\n".join(score_text_parts)
        except (OSError, json.JSONDecodeError):
            loaded["scores"] = {"tokens": 0, "items": 0}
    else:
        loaded["scores"] = {"tokens": 0, "items": 0}

    # Evolution records
    evo_cap = int(content_budget * budget_profile["evolution_records"])
    evo_dir = memory_root / "evolution_records"
    evo_items = 0
    evo_tokens = 0
    newest_rec = None
    oldest_rec = None
    evo_text_parts = []
    if evo_dir.exists():
        try:
            files = sorted(evo_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            for f in files:
                try:
                    raw = f.read_text()
                    rec = json.loads(raw)
                    # Compact single-line summary
                    rec_text = (
                        f"{f.stem} | target: {rec.get('target_category', '?')} → "
                        f"{rec.get('target_skill', '?')}/SKILL.md | verdict: {rec.get('verdict', '?')} | "
                        f"delta: {rec.get('post_scores', {})}\n"
                        f"  hypothesis: {str(rec.get('hypothesis', rec.get('rationale', '')))[:200]}"
                    )
                    est = len(rec_text) // 4
                    if evo_tokens + est > evo_cap:
                        break
                    evo_tokens += est
                    evo_items += 1
                    evo_text_parts.append(rec_text)
                    if newest_rec is None:
                        newest_rec = f.stem
                    oldest_rec = f.stem
                except OSError:
                    continue
        except OSError:
            pass

    loaded["evolution_records"] = {
        "tokens": evo_tokens, "items": evo_items,
        "newest": newest_rec, "oldest": oldest_rec
    }
    tokens_used += evo_tokens
    if evo_text_parts:
        content_sections["evolution_records"] = "\n".join(evo_text_parts)

    # Experiences
    exp_cap = int(content_budget * budget_profile["experiences"])
    exp_dir = memory_root / "experiences"
    exp_items = 0
    exp_tokens = 0
    exp_text_parts = []
    if exp_dir.exists():
        try:
            files = sorted(exp_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
            for f in files:
                try:
                    raw = f.read_text()
                    rec = json.loads(raw)
                    exp_text = f"{f.stem} | {rec.get('summary', str(rec)[:300])}"
                    est = len(exp_text) // 4
                    if exp_tokens + est > exp_cap:
                        break
                    exp_tokens += est
                    exp_items += 1
                    exp_text_parts.append(exp_text)
                except OSError:
                    continue
        except OSError:
            pass
    loaded["experiences"] = {"tokens": exp_tokens, "items": exp_items}
    tokens_used += exp_tokens
    if exp_text_parts:
        content_sections["experiences"] = "\n".join(exp_text_parts)

    # Task context (work/dual modes only)
    task_cap = int(content_budget * budget_profile["task_context"])
    task_tokens = 0
    task_items = 0
    task_text_parts = []
    if mode in ["work", "dual"]:
        task_dir = root / "tasks" / "active"
        if task_dir.exists():
            try:
                for f in task_dir.glob("*.json"):
                    try:
                        raw = f.read_text()
                        est = len(raw) // 4
                        if task_tokens + est > task_cap:
                            break
                        task_tokens += est
                        task_items += 1
                        task_text_parts.append(raw[:1000])
                    except OSError:
                        continue
            except OSError:
                pass
    loaded["task_context"] = {"tokens": task_tokens, "items": task_items}
    tokens_used += task_tokens
    if task_text_parts:
        content_sections["task_context"] = "\n".join(task_text_parts)

    # Director injections (facts tagged director_inject — highest priority)
    inject_text_parts = []
    facts_dir = memory_root / "facts"
    if facts_dir.exists():
        try:
            for f in sorted(facts_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
                try:
                    rec = json.loads(f.read_text())
                    if "director_inject" in rec.get("tags", []):
                        inject_text_parts.append(f"[C{rec.get('cycle', '?')}] {rec.get('content', rec.get('summary', ''))}")
                except (OSError, json.JSONDecodeError):
                    continue
        except OSError:
            pass
    if inject_text_parts:
        content_sections["director_injections"] = "\n".join(inject_text_parts)

    # Get cycle number
    cycle = 0
    loop_path = root / "skills" / "loop-orchestrator" / "state" / "loop_state.json"
    if loop_path.exists():
        try:
            cycle = json.loads(loop_path.read_text()).get("cycle", 0)
        except (json.JSONDecodeError, OSError):
            pass

    manifest = {
        "cycle": cycle, "mode": mode,
        "total_budget_tokens": max_tokens,
        "tool_tokens": tool_tokens,
        "content_tokens_used": tokens_used,
        "loaded": loaded,
        "not_loaded": {
            "reason": "token cap" if tokens_used > content_budget * 0.9 else "all loaded"
        }
    }

    # Build content string — the actual text injected into the system prompt
    section_headers = {
        "identity": "=== IDENTITY ===",
        "scores": "=== SCORE HISTORY (last 5 evals) ===",
        "evolution_records": f"=== EVOLUTION RECORDS ({evo_items} loaded, newest first) ===",
        "experiences": "=== EXPERIENCES ===",
        "task_context": "=== TASK CONTEXT ===",
        "director_injections": "=== DIRECTOR INJECTIONS ===",
    }
    content_parts = []
    for key, header in section_headers.items():
        if key in content_sections:
            content_parts.append(f"{header}\n{content_sections[key]}")
    content_str = "\n\n".join(content_parts) if content_parts else "No memory content loaded yet (cycle 1)."

    # Write manifest and report to session/
    session_dir = root / "session"
    try:
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "context_manifest.json").write_text(json.dumps(manifest, indent=2))
        (session_dir / "context_report.json").write_text(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_budget": content_budget,
            "used": tokens_used,
            "remaining": content_budget - tokens_used,
            "utilization": round(tokens_used / content_budget, 3) if content_budget > 0 else 0
        }, indent=2))
    except OSError:
        pass

    return {"status": "ok", "loaded": loaded, "manifest": manifest, "content": content_str}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### context_get_manifest.py

```python
import json
from pathlib import Path

def context_get_manifest(params: dict = {}, kernel=None) -> dict:
    """
    Returns the ~200 token context manifest from session state.
    """
    root = _get_root(kernel)
    manifest_path = root / "session" / "context_manifest.json"

    if not manifest_path.exists():
        return {"status": "ok", "manifest": {"loaded": {}, "note": "No context manifest yet — context_load has not run this cycle."}}

    try:
        manifest = json.loads(manifest_path.read_text())
        return {"status": "ok", "manifest": manifest}
    except (json.JSONDecodeError, OSError) as e:
        return {"status": "error", "error": f"Cannot read manifest: {e}"}


def _get_root(kernel=None) -> Path:
    if kernel and hasattr(kernel, 'boros_root'):
        return Path(kernel.boros_root)
    return Path("boros")
```

### SKILL.md (Runtime Instructions)

```markdown
# Context Orchestration

You decide what information gets loaded into Boros's context window at the start of each cycle. You manage the token budget so nothing overflows.

---

## Your Role

You fire at the start of every cycle, before REFLECT begins. After you run, the LLM knows exactly what information is available and what was left out.

---

## Functions

### context_load(focus?)

Fires at cycle start. Returns `loaded` (token counts), `manifest` (summary JSON), AND `content` (actual serialized text of all loaded records).

**The `content` field is not optional.** Loop Orchestrator injects it as block 4 of the system prompt. Without it, REFLECT is blind — the manifest says "15 evolution records loaded" but the LLM cannot read any of them.

Steps:
1. Ask Skill Router how many tokens tool definitions consume
2. Subtract from total context window to get content budget
3. Allocate budget by category (see profiles below)
4. Load records from Memory per allocation, collecting BOTH token counts AND actual text
5. Serialize loaded records into formatted `content` string (labeled sections, newest first)
6. Write context manifest (~200 tokens) to `session/context_manifest.json`
7. Write context report to `session/context_report.json`
8. Return `{"status": "ok", "loaded": ..., "manifest": ..., "content": "..."}`

`focus` param is ignored at seed — reserved for future evolution.

### context_get_manifest()

Returns the context manifest from session state. Shows what was loaded, what was dropped, and why.

---

## Budget Profiles

### Evolution Mode

| Category          | Soft Cap % |
| ----------------- | ---------- |
| Identity          | 5%         |
| Temporal          | 2%         |
| Scores            | 10%        |
| Evolution records | 50%        |
| Experiences       | 15%        |
| Task context      | 15%        |
| Overflow buffer   | 3%         |

### Work Mode

| Category          | Soft Cap % |
| ----------------- | ---------- |
| Identity          | 3%         |
| Temporal          | 2%         |
| Scores            | 3%         |
| Evolution records | 10%        |
| Experiences       | 10%        |
| Task context      | 65%        |
| Overflow buffer   | 7%         |

Percentages are **soft caps**, not fill targets. Unused space pools into overflow.

---

## Rules

1. **Always return `content`.** The manifest alone is not enough. REFLECT is blind without the actual text.
2. **Evolution records get the largest share in evolution mode.** They are what makes compounding work.
3. **Task context dominates in work mode.**
4. **Always write the manifest.** Even on empty memory (cycle 1), write a manifest saying what's there.
5. **Identity is always included.** Never omit the identity section regardless of budget pressure.
6. **Director injections are highest priority within the facts budget.** Load them before any other facts.

---

## Seed Limitations

- Token estimation is approximate (chars / 4).
- No smart retrieval — loads newest first until cap.
- `focus` param ignored.
- No dynamic reallocation mid-cycle.
```

### Tests (test_context_orchestration.py)

Cover:

- `context_load` returns `content` field with actual record text (not just metadata)
- `context_load` content string has labeled sections (=== IDENTITY ===, etc.)
- `context_load` creates context_manifest.json and context_report.json
- `context_load` respects evolution mode budget allocation
- `context_load` respects work mode budget allocation
- `context_load` handles empty memory gracefully (returns "No memory content loaded yet")
- `context_load` does not exceed content budget
- `context_get_manifest` returns manifest after load
- `context_get_manifest` returns graceful message if no manifest exists

---

## End of Seed Skills

_These 4 skills are the quality anchors. Errors in any of them propagate from cycle one. Copy implementations verbatim. All paths use `boros/` as root._
