import os, sys, time, json, uuid, datetime, shutil
import random

boros_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, boros_root)

from boros.adapters import load_adapter
from boros.kernel import BorosKernel
from boros.tool_schemas import TOOL_SCHEMAS
from tool_dispatcher import ToolDispatcher

class EvalGenerator:
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.shared_dir = os.path.join(self.base_dir, "shared")
        self.requests_dir = os.path.join(self.shared_dir, "requests")
        self.results_dir = os.path.join(self.shared_dir, "results")
        self.sandboxes_dir = os.path.join(self.base_dir, "sandboxes")
        self.world_model_path = os.path.join(boros_root, "boros", "world_model.json")
        self.config_path = os.path.join(boros_root, "boros", "config.json")
        
        for d in [self.requests_dir, self.results_dir, self.sandboxes_dir]:
            os.makedirs(d, exist_ok=True)
            
        with open(self.config_path) as f:
            self.config = json.load(f)
            
        try:
            self.llm = load_adapter(self.config["providers"]["meta_eval_api"])
            self.actor_llm = load_adapter(self.config["providers"]["evolution_api"])
        except Exception as e:
            print(f"[EvalGenerator] Could not load LLM adapter: {e}")
            self.llm = None
            self.actor_llm = None

        with open(self.world_model_path) as f:
            self.world_model = json.load(f)
            
        self._write_ready_file()

    def _write_ready_file(self):
        with open(os.path.join(self.shared_dir, ".ready"), "w") as f:
            f.write("ready")

    def run(self):
        print("Eval Generator listening for requests...")
        while True:
            self._poll_requests()
            time.sleep(2)

    def _poll_requests(self):
        for req_file in os.listdir(self.requests_dir):
            if req_file.endswith(".json"):
                req_path = os.path.join(self.requests_dir, req_file)
                self._process_request(req_path)

    def _generate_task(self, category_id):
        cat = self.world_model["categories"].get(category_id)
        if not cat or not self.llm: return "Write a script that prints Hello World to output.txt."
        
        seed = cat.get("seed_prompts", {}).get("edge", "Test reasoning.")
        prompt = f"Create a concrete, verifiable programming puzzle or logic task based on this seed: '{seed}'. The task must be executable in a python sandbox and verifiable by checking file outputs. Output just the task prompt."
        try:
            res = self.llm.complete([{"role": "user", "content": prompt}], system="Just write the task.")
            text = "".join(b.get("text", "") for b in res.get("content", []) if b.get("type") == "text")
            return text.strip() or "Write a python script to output.txt"
        except:
            return "Write a python script to output.txt that adds two numbers."

    def _grade_sandbox(self, transcript, category_id, workspace_dir):
        if not self.llm: 
            return {"score": 0.5, "quality_reason": "No LLM adapter loaded", "outcome_details": "N/A"}
        
        # Check actual files in workspace to provide outcome details
        if workspace_dir and os.path.exists(workspace_dir):
            file_list = os.listdir(workspace_dir)
            files_str = f"Files created: {', '.join(file_list)}" if file_list else "No files created."
        else:
            files_str = "No workspace details found."

        cat = self.world_model["categories"].get(category_id, {})
        level_4 = cat.get("rubric", {}).get("level_4", "Excellent")
        prompt = (f"Review this sandbox transcript for the category '{category_id}'.\n\n"
                  f"Level 4 criteria: {level_4}\n\nTranscript:\n{transcript}\n\n"
                  f"Workspace evidence: {files_str}\n\n"
                  f"Provide actionable structural feedback. Did the agent output real code? Did it finish the task? "
                  f"Score from 0.0 to 1.0. Output ONLY a valid JSON object: {{\"score\": <float between 0.0 and 1.0>, \"quality_reason\": \"...\", \"outcome_details\": \"...\"}}")
        try:
            res = self.llm.complete([{"role": "user", "content": prompt}])
            text = "".join(b.get("text", "") for b in res.get("content", []) if b.get("type") == "text")
            import re
            match = re.search(r'\{[^}]+\}', text, re.DOTALL)
            if match:
                data = json.loads(match.group())
                return {
                    "score": float(data.get("score", 0.5)),
                    "quality_reason": data.get("quality_reason", "No reason given"),
                    "outcome_details": data.get("outcome_details", files_str)
                }
        except:
            pass
        return {"score": 0.5, "quality_reason": "Grading failed", "outcome_details": files_str}

    def _process_request(self, req_path):
        try:
            with open(req_path, "r") as f:
                req = json.load(f)
                
            eval_id = f"eval-{uuid.uuid4().hex[:8]}"
            print(f"[EvalGenerator] Processing {eval_id} for cycle {req.get('cycle', 0)}")
            
            categories = req.get("categories") or list(self.world_model["categories"].keys())
            scores = {}
            total_score = 0.0
            
            sandbox_dir = os.path.join(self.sandboxes_dir, eval_id)
            for cat_id in categories:
                cat_dir = os.path.join(sandbox_dir, cat_id)
                workspace_dir = os.path.join(cat_dir, "workspace")
                os.makedirs(workspace_dir, exist_ok=True)
                
                task = self._generate_task(cat_id)
                kernel = BorosKernel()
                # Force reload to ensure we pick up the latest code modified by the main agent loop
                for skill_name in kernel.manifest.get("skills", {}):
                    kernel.reload_skill(skill_name)

                dispatcher = ToolDispatcher(workspace_dir, kernel)
                
                # Mini Agent Loop Simulation
                messages = [{"role": "user", "content": f"Task: {task}\nSolve this using your tools."}]
                
                # Inject actual Boros tools for evaluation
                allowed_skills = ["reasoning", "scratchpad", "tool-use", "web-research"]
                tools = []
                for skill_name in allowed_skills:
                    if skill_name in kernel.manifest.get("skills", {}):
                        s_info = kernel.manifest["skills"][skill_name]
                        for func_name in s_info.get("provided_functions", []):
                            if func_name in TOOL_SCHEMAS:
                                tools.append(TOOL_SCHEMAS[func_name])
                                
                # Keep basic stub tools so the LLM doesn't get confused if it tries normal file operations
                tools.extend([
                    {"name": "write_file", "description": "Write a file", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}}},
                    {"name": "read_file", "description": "Read a file", "input_schema": {"type": "object", "properties": {"path": {"type": "string"}}}}
                ])
                
                transcript = f"Task: {task}\n\n"
                
                if self.actor_llm:
                    for _ in range(5): # Limit iterations for eval
                        try:
                            res = self.actor_llm.complete(messages, tools=tools)
                            content = res.get("content", [])
                            messages.append({"role": "assistant", "content": content})
                            
                            has_tool = False
                            tool_results = []
                            for b in content:
                                if b.get("type") == "text":
                                    transcript += f"Agent: {b.get('text')}\n"
                                if b.get("type") == "tool_use":
                                    has_tool = True
                                    result = dispatcher.dispatch(b["name"], b["input"])
                                    r_str = json.dumps(result)
                                    transcript += f"Tool {b['name']}: {r_str}\n"
                                    tool_results.append({"type": "tool_result", "tool_use_id": b["id"], "content": r_str})
                                    
                            if not has_tool:
                                break
                            messages.append({"role": "user", "content": tool_results})
                        except Exception as loop_e:
                            transcript += f"Error: {loop_e}\n"
                            break

                score_data = self._grade_sandbox(transcript, cat_id, workspace_dir)
                score = score_data["score"]
                scores[cat_id] = {
                    "outcome_score": score, 
                    "quality_score": score,
                    "outcome_weight": 0.5, 
                    "quality_weight": 0.5,
                    "quality_reason": score_data["quality_reason"],
                    "outcome_details": score_data["outcome_details"]
                }
                total_score += score
                
            shutil.rmtree(sandbox_dir, ignore_errors=True)
            composite_score = total_score / len(categories) if categories else 0.0
            
            result = {
                "request_id": req.get("request_id", "unknown"),
                "eval_id": eval_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "cycle": req.get("cycle", 0),
                "scores": {k: v["outcome_score"] for k,v in scores.items()},
                "composite": composite_score,
                "difficulty_level": 5,
                "scoring_breakdown": scores
            }
            
            res_path = os.path.join(self.results_dir, f"{eval_id}.json")
            with open(res_path, "w") as f:
                json.dump(result, f, indent=2)
                
            os.remove(req_path)
            print(f"[EvalGenerator] Finished eval {eval_id} with score {composite_score:.2f}")
        except Exception as e:
            print(f"[EvalGenerator] Error processing request: {e}")
            if os.path.exists(req_path):
                os.remove(req_path)

if __name__ == "__main__":
    generator = EvalGenerator()
    generator.run()
