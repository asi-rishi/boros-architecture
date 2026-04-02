import os
import time
import json
import uuid
import datetime
import shutil
from tool_dispatcher import ToolDispatcher

class EvalGenerator:
    def __init__(self):
        self.base_dir = os.path.dirname(__file__)
        self.shared_dir = os.path.join(self.base_dir, "shared")
        self.requests_dir = os.path.join(self.shared_dir, "requests")
        self.results_dir = os.path.join(self.shared_dir, "results")
        self.sandboxes_dir = os.path.join(self.base_dir, "sandboxes")
        
        for d in [self.requests_dir, self.results_dir, self.sandboxes_dir]:
            os.makedirs(d, exist_ok=True)
            
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

    def _process_request(self, req_path):
        try:
            with open(req_path, "r") as f:
                req = json.load(f)
                
            eval_id = f"eval-{uuid.uuid4().hex[:8]}"
            
            # 1. Create sandbox
            sandbox_dir = os.path.join(self.sandboxes_dir, eval_id)
            workspace_dir = os.path.join(sandbox_dir, "workspace")
            os.makedirs(workspace_dir, exist_ok=True)
            
            # 2. Simulate task execution with tool dispatch and scoring
            dispatcher = ToolDispatcher(workspace_dir)
            dispatcher.dispatch("write_file", {"path": "check.txt", "content": "test"})
            
            # 3. outcome verification mock
            outcome_score = 1.0 if os.path.exists(os.path.join(workspace_dir, "check.txt")) else 0.0
            
            # 4. Destroy sandbox
            shutil.rmtree(sandbox_dir, ignore_errors=True)
            
            # 5. Write result
            result = {
                "request_id": req.get("request_id", "unknown"),
                "eval_id": eval_id,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "cycle": req.get("cycle", 0),
                "scores": {
                    "reasoning_architecture": 0.85
                },
                "composite": 0.85,
                "difficulty_level": 2,
                "tests_per_category": 3,
                "scoring_breakdown": {
                    "reasoning_architecture": {
                        "outcome_score": outcome_score,
                        "quality_score": 0.6,
                        "outcome_weight": 0.6,
                        "quality_weight": 0.4
                    }
                }
            }
            
            res_path = os.path.join(self.results_dir, f"{eval_id}.json")
            with open(res_path, "w") as f:
                json.dump(result, f, indent=2)
                
            os.remove(req_path)
            print(f"Processed {req_path} -> {res_path}")
        except Exception as e:
            print(f"Error processing request: {e}")
            if os.path.exists(req_path):
                os.remove(req_path)

if __name__ == "__main__":
    generator = EvalGenerator()
    generator.run()
