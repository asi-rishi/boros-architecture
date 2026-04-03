"""
Boros Agent Loop - The core LLM <-> Tool dispatch engine.

This is the beating heart of Boros. It sends messages to the LLM,
parses tool_use responses, dispatches them through the kernel registry,
and loops until the LLM ends its turn or limits are reached.
"""

import json
import time
import traceback
from pathlib import Path


class AgentLoop:
    def __init__(self, kernel, log_callback=None):
        self.kernel = kernel
        self.log = log_callback or print
        self.max_tool_calls = kernel.config.get("max_tool_calls_per_cycle", 100)
        self.max_cycle_minutes = kernel.config.get("max_cycle_duration_minutes", 10)
        self.boros_root = kernel.boros_root

    # ────────────────────────────────────────────
    # System Prompt Construction
    # ────────────────────────────────────────────

    def build_system_prompt(self):
        """Load BOROS.md + live state into the system prompt."""
        parts = []

        # 1. Primary instruction set
        boros_md = self.boros_root / "BOROS.md"
        if boros_md.exists():
            parts.append(boros_md.read_text(encoding="utf-8"))

        # 2. Current loop state
        state_file = self.boros_root / "boros" / "session" / "loop_state.json"
        if state_file.exists():
            try:
                state = json.loads(state_file.read_text())
                parts.append(f"## Current Loop State\n```json\n{json.dumps(state, indent=2)}\n```")
            except Exception:
                pass

        # 3. Identity
        id_file = self.boros_root / "boros" / "skills" / "identity" / "state" / "identity.json"
        if id_file.exists():
            try:
                identity = json.loads(id_file.read_text())
                parts.append(f"## Identity\n```json\n{json.dumps(identity, indent=2)}\n```")
            except Exception:
                pass

        # 4. Recent scores
        score_dir = self.boros_root / "boros" / "evals" / "scores"
        if score_dir.exists():
            score_files = sorted(score_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True)[:3]
            if score_files:
                scores_text = []
                for sf in score_files:
                    try:
                        scores_text.append(json.loads(sf.read_text()))
                    except Exception:
                        pass
                if scores_text:
                    parts.append(f"## Recent Evaluation Scores\n```json\n{json.dumps(scores_text, indent=2)}\n```")

        # 5. Score history (last 5 entries)
        score_hist = self.boros_root / "boros" / "memory" / "score_history.jsonl"
        if score_hist.exists():
            try:
                lines = score_hist.read_text().strip().split("\n")
                recent = lines[-5:] if len(lines) > 5 else lines
                entries = [json.loads(l) for l in recent if l.strip()]
                if entries:
                    parts.append(f"## Score History (last {len(entries)} entries)\n```json\n{json.dumps(entries, indent=2)}\n```")
            except Exception:
                pass

        # 6. Active hypothesis
        hyp_file = self.boros_root / "boros" / "session" / "hypothesis.json"
        if hyp_file.exists():
            try:
                parts.append(f"## Active Hypothesis\n```json\n{hyp_file.read_text()}\n```")
            except Exception:
                pass

        # 7. High-water marks
        hw_file = self.boros_root / "boros" / "skills" / "eval-bridge" / "state" / "high_water_marks.json"
        if hw_file.exists():
            try:
                parts.append(f"## High-Water Marks\n```json\n{hw_file.read_text()}\n```")
            except Exception:
                pass

        return "\n\n---\n\n".join(parts)

    # ────────────────────────────────────────────
    # Tool Manifest
    # ────────────────────────────────────────────

    def build_tools(self):
        """Build tool list from schemas, filtered to registered functions."""
        from boros.tool_schemas import TOOL_SCHEMAS
        tools = []
        for func_name in self.kernel.registry:
            if func_name in TOOL_SCHEMAS:
                tools.append(TOOL_SCHEMAS[func_name])
        return tools

    # ────────────────────────────────────────────
    # Tool Dispatch
    # ────────────────────────────────────────────

    def dispatch_tool(self, name, params):
        """Dispatch a tool call to the kernel registry."""
        if name not in self.kernel.registry:
            return {"status": "error", "message": f"Unknown tool: {name}"}
        try:
            result = self.kernel.registry[name](params or {}, self.kernel)
            return result
        except Exception as e:
            tb = traceback.format_exc()
            self.log(f"[ERROR] Tool {name} crashed: {e}")
            return {"status": "error", "message": str(e), "traceback": tb}

    # ────────────────────────────────────────────
    # Single Cycle
    # ────────────────────────────────────────────

    def run_cycle(self):
        """Run one full evolution cycle (REFLECT -> EVOLVE -> EVAL)."""
        system = self.build_system_prompt()
        tools = self.build_tools()

        messages = [{"role": "user", "content": self._cycle_prompt()}]

        tool_call_count = 0
        cycle_start = time.time()

        self.log("[CYCLE] Starting evolution cycle...")
        status = "completed"

        try:
            while tool_call_count < self.max_tool_calls:
                # Time limit check
                elapsed_min = (time.time() - cycle_start) / 60
                if elapsed_min > self.max_cycle_minutes:
                    self.log(f"[CYCLE] Time limit ({self.max_cycle_minutes}m) reached.")
                    status = "timeout"
                    break

                # Call LLM
                try:
                    response = self.kernel.evolution_llm.complete(messages, tools, system)
                except Exception as e:
                    self.log(f"[ERROR] LLM call failed: {e}")
                    self.log(traceback.format_exc())
                    status = "error"
                    raise  # Let the continuous loop catch this and trigger the cooldown sleep
    
                content = response.get("content", [])
                stop_reason = response.get("stop_reason", "end_turn")
                usage = response.get("usage", {})
    
                # Log text output
                for block in content:
                    if block.get("type") == "text" and block.get("text"):
                        self.log(f"[BOROS] {block['text'][:800]}")
    
                # Log usage
                if usage:
                    self.log(f"[TOKENS] in={usage.get('input_tokens', '?')} out={usage.get('output_tokens', '?')}")
    
                # Append assistant response
                messages.append({"role": "assistant", "content": content})
    
                # Natural stop
                if stop_reason == "end_turn":
                    self.log("[CYCLE] LLM ended turn naturally.")
                    break
    
                # Dispatch tool calls
                tool_results = []
                for block in content:
                    if block.get("type") == "tool_use":
                        name = block["name"]
                        inp = block.get("input", {})
                        tid = block["id"]
    
                        if name == "evolve_propose":
                            desc = inp.get("description", "")
                            self.log(f"\n========================================")
                            self.log(f"📝 [PROPOSAL CREATED]: {desc}")
                            self.log(f"========================================\n")
                            self.log(f"[TOOL] → {name}({json.dumps(inp, default=str)[:300]})")
                        elif name == "tool_file_edit_diff":
                            self.log(f"\n========================================")
                            self.log(f"⚙️ [CODE MUTATION] Targeting: {inp.get('target_file')}")
                            for i, chunk in enumerate(inp.get("replacement_chunks", [])):
                                self.log(f"\n--- Chunk {i+1} ---")
                                target_lines = chunk.get("target_content", "").split("\n")
                                replace_lines = chunk.get("replacement_content", "").split("\n")
                                for line in target_lines: self.log(f"[-] {line}")
                                for line in replace_lines: self.log(f"[+] {line}")
                            self.log(f"========================================\n")
                            self.log(f"[TOOL] → {name}(...)")
                        else:
                            self.log(f"[TOOL] → {name}({json.dumps(inp, default=str)[:300]})")
    
                        result = self.dispatch_tool(name, inp)
                        result_str = json.dumps(result, default=str)
                        
                        if name in ("evolve_propose", "tool_file_edit_diff"):
                            self.log(f"[TOOL] ← {result_str}") # print full result for these
                        else:
                            self.log(f"[TOOL] ← {result_str[:400]}")
    
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tid,
                            "content": result_str
                        })
                        tool_call_count += 1
    
                if not tool_results:
                    self.log("[CYCLE] No tool calls found. Ending.")
                    break
    
                messages.append({"role": "user", "content": tool_results})
    
        finally:
            # Log cycle end to file
            log_file = self.boros_root / "boros" / "logs" / "cycles.log"
            log_file.parent.mkdir(parents=True, exist_ok=True)
            with open(log_file, "a") as f:
                f.write(f"Cycle ended. status={status} tool_calls={tool_call_count}\n")
                f.flush()

        self.log(f"[CYCLE] Finished. {tool_call_count} tool calls.")
        return tool_call_count

    # ────────────────────────────────────────────
    # Continuous Loop
    # ────────────────────────────────────────────

    def run_continuous(self, should_pause=None, on_cycle_complete=None):
        """Run evolution cycles until paused."""
        cycle_num = 0
        fail_count = 0
        import random
        while True:
            if should_pause and should_pause():
                self.log("[LOOP] Pause requested.")
                break

            cycle_num += 1
            self.log(f"\n{'='*60}")
            self.log(f"  EVOLUTION CYCLE {cycle_num}")
            self.log(f"{'='*60}\n")

            try:
                tc = self.run_cycle()
                if on_cycle_complete:
                    on_cycle_complete(cycle_num, tc)
                fail_count = 0  # Reset backoff on success
            except Exception as e:
                self.log(f"[ERROR] Cycle {cycle_num} failed: {e}")
                self.log(traceback.format_exc())
                fail_count += 1
                wait_time = min(300, 30 * (2 ** (fail_count - 1)))
                jitter = random.uniform(0, 5)
                total_wait = wait_time + jitter
                self.log(f"[RATE_LIMIT] API limit hit. Exponential backoff for {total_wait:.1f}s (Fail #{fail_count})")
                time.sleep(total_wait)

    # ────────────────────────────────────────────
    # Cycle Prompt
    # ────────────────────────────────────────────

    def _cycle_prompt(self):
        return (
            "Begin a new evolution cycle. You are Boros — an autonomous, self-evolving AI substrate.\n\n"
            "Execute the 3-stage loop:\n\n"
            "## STAGE 1: REFLECT\n"
            "1. `loop_start` — initialize cycle state\n"
            "2. `eval_read_scores` — read your latest evaluation scores\n"
            "3. `reflection_analyze_trace` — identify trends and weaknesses\n"
            "4. `reflection_write_hypothesis` — formulate an improvement hypothesis\n"
            "5. `loop_advance_stage` — transition to EVOLVE\n\n"
            "## STAGE 2: EVOLVE\n"
            "6. `evolve_orient` — survey weak areas and pick a target\n"
            "7. `forge_snapshot` — snapshot the target skill before changes\n"
            "8. Read the target file with `tool_terminal` (e.g. `type boros\\skills\\<skill>\\functions\\<file>.py`)\n"
            "9. Write REAL Python code improvements using `tool_file_edit_diff`\n"
            "10. `forge_validate` — check syntax of the modified skill\n"
            "11. `evolve_propose` — create a formal proposal\n"
            "12. `review_proposal` — submit to the Meta-Evaluation review board (AUTO-ROLLBACKS IF REJECTED)\n"
            "13. If approved: `evolve_apply` to commit and trigger dynamic HOT-RELOAD.\n"
            "14. `loop_advance_stage` — transition to EVAL\n\n"
            "## STAGE 3: EVAL\n"
            "15. `eval_request` — request sandbox evaluation (returns a request_id)\n"
            "16. `eval_read_scores` — read results (YOU MUST pass the returned request_id into eval_id so it waits for the result!)\n"
            "17. `eval_check_regression` — compare to high-water marks\n"
            "18. `eval_update_high_water` — update if improved\n"
            "19. `identity_update` — (IF IMPROVED) update your self_narrative and capabilities to reflect your new mastery\n"
            "20. `memory_commit_archival` — save learnings\n"
            "21. `loop_end_cycle` — finalize\n\n"
            "IMPORTANT: Make REAL code improvements or Skill File instruction improvements. Read actual files, write actual diffs. "
            "Do not mock or simulate. Every tool call should produce real side-effects.\n"
            "Focus on improving the weakest-scoring skill functions — make them more capable."
        )
