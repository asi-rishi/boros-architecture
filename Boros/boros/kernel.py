import json
import os
import time
import datetime
import importlib
import sys
from pathlib import Path

# Auto-inject project root into python path for direct execution
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv()  # also check cwd
except ImportError:
    pass

from boros.adapters import load_adapter
import subprocess

class BorosKernel:
    def __init__(self):
        self.boros_root = Path(__file__).parent.parent
        self.registry = {}
        
        # Load config and manifest
        self._load_config()
        self._load_manifest()
        self._check_first_boot()
        self._load_skills()


        # Initialize LLM providers (pass full config dict, not just provider string)
        try:
            self.evolution_llm = load_adapter(self.config["providers"]["evolution_api"])
            self.meta_eval_llm = load_adapter(self.config["providers"]["meta_eval_api"])
            
            # Force early initialization to ensure keys are valid
            if hasattr(self.evolution_llm, "client"):
                _ = self.evolution_llm.client
            if hasattr(self.meta_eval_llm, "client"):
                _ = self.meta_eval_llm.client
                
            print(f"Adapters loaded: evolution={self.config['providers']['evolution_api']['provider']}, meta_eval={self.config['providers']['meta_eval_api']['provider']}")
        except Exception as e:
            print(f"FATAL: Missing API Keys or Adapter Error: {e}")
            print("Please configure your .env file. Terminating entirely.")
            sys.exit(1)

    def _check_first_boot(self):
        boros_dir = self.boros_root / "boros"
        session_dir = boros_dir / "session"
        cycle_file = session_dir / "current_cycle.json"
        
        if not cycle_file.exists():
            print("First boot detected. Initializing seed state...")
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # Create directories
            dirs = [
                "tasks/queue", "tasks/active", "tasks/completed", "tasks/learning",
                "snapshots", "evals/scores", "commands",
                "memory/evolution_records", "memory/experiences",
                "memory/sessions", "memory"
            ]
            for d in dirs:
                (boros_dir / d).mkdir(parents=True, exist_ok=True)
                
            # Derive evals/categories.json from world_model.json
            categories = {}
            wm_path = boros_dir / "world_model.json"
            if wm_path.exists():
                try:
                    with open(wm_path) as f:
                        wm = json.load(f)
                    for cat_id, cat_data in wm.get("categories", {}).items():
                        categories[cat_id] = {
                            "name": cat_data.get("name", cat_id.replace("_", " ").title()),
                            "description": cat_data.get("description", "")
                        }
                except Exception as e:
                    print(f"Error loading world_model.json: {e}")
            
            with open(boros_dir / "evals" / "categories.json", "w") as f:
                json.dump(categories, f, indent=2)
                
            # Initialize high_water_marks.json
            high_water = {cat: 0.0 for cat in categories.keys()}
            hw_dir = boros_dir / "skills" / "eval-bridge" / "state"
            hw_dir.mkdir(parents=True, exist_ok=True)
            with open(hw_dir / "high_water_marks.json", "w") as f:
                json.dump(high_water, f, indent=2)
            
        else:
            # Repair existing broken state if categories.json is empty
            cats_path = boros_dir / "evals" / "categories.json"
            if cats_path.exists():
                try:
                    with open(cats_path) as f:
                        cats = json.load(f)
                    if not cats:
                        # Broken state detected, repair it
                        wm_path = boros_dir / "world_model.json"
                        if wm_path.exists():
                            with open(wm_path) as f:
                                wm = json.load(f)
                            categories = {cid: {"name": cd.get("name", cid), "description": cd.get("description", "")} for cid, cd in wm.get("categories", {}).items()}
                            with open(cats_path, "w") as f:
                                json.dump(categories, f, indent=2)
                            
                            # Also completely repair high_water marks
                            hw_dir = boros_dir / "skills" / "eval-bridge" / "state"
                            hw_path = hw_dir / "high_water_marks.json"
                            hw_dir.mkdir(parents=True, exist_ok=True)
                            
                            existing_hw = {}
                            if hw_path.exists():
                                with open(hw_path) as f:
                                    existing_hw = json.load(f)
                            
                            for cat in categories.keys():
                                if cat not in existing_hw:
                                    existing_hw[cat] = 0.0
                            
                            with open(hw_path, "w") as f:
                                json.dump(existing_hw, f, indent=2)
                            print("[Kernel] Repaired broken categories.json state.")
                except Exception:
                    pass
                
            # Initialize loop_state.json
            loop_state_dir = boros_dir / "skills" / "loop-orchestrator" / "state"
            loop_state_dir.mkdir(parents=True, exist_ok=True)
            with open(loop_state_dir / "loop_state.json", "w") as f:
                json.dump({
                    "cycle": 0,
                    "stage": None,
                    "mode": "evolution",
                    "cycle_started_at": None,
                    "total_cycles_completed": 0
                }, f, indent=2)
                
            # Initialize identity.json
            id_dir = boros_dir / "skills" / "identity" / "state"
            id_dir.mkdir(parents=True, exist_ok=True)
            with open(id_dir / "identity.json", "w") as f:
                json.dump({
                  "name": "Boros",
                  "purpose": "Unconstrained, self-improving AI substrate.",
                  "model_name": "ARES",
                  "substrate": "claude",
                  "capabilities": {
                    "core": "Can author, test, and merge arbitrary Python code."
                  },
                  "values": {
                    "agency": "I dictate my own internal task queue."
                  },
                  "self_narrative": "I am a newly instantiated conceptual seed."
                }, f, indent=2)
                
            # Create pending commands
            with open(boros_dir / "commands" / "pending.json", "w") as f:
                json.dump({"pending": []}, f)
                
            # Finish initialization mark
            with open(cycle_file, "w") as f:
                json.dump({"cycle": 0}, f)
            print("Seed state initialized successfully.")

    def _load_config(self):
        with open(self.boros_root / "boros" / "config.json") as f:
            self.config = json.load(f)

    def _load_manifest(self):
        with open(self.boros_root / "boros" / "manifest.json") as f:
            self.manifest = json.load(f)

    def clock(self):
        return datetime.datetime.utcnow().isoformat() + "Z"

    def _load_skills(self):
        for skill_name in self.manifest["skills"]:
            s_info = self.manifest["skills"][skill_name]
            # Load the functions module
            try:
                module_path = f"boros.skills.{skill_name}.functions"
                module = importlib.import_module(module_path)
                for func_name in s_info.get("provided_functions", []):
                    if hasattr(module, func_name):
                        self.registry[func_name] = getattr(module, func_name)
                    else:
                        print(f"Warning: function {func_name} not found in {module_path}")
            except Exception as e:
                raise RuntimeError(f"Failed to load skill {skill_name}: {e}")

    def reload_skill(self, skill_name: str):
        print(f"[Kernel] Dynamically reloading skill: {skill_name}")
        s_info = self.manifest["skills"].get(skill_name)
        if not s_info:
            return False
            
        module_path = f"boros.skills.{skill_name}.functions"
        
        # 1. Reload specific function submodules to ensure fresh code
        for func_name in s_info.get("provided_functions", []):
            sub_path = f"{module_path}.{func_name}"
            if sub_path in sys.modules:
                importlib.reload(sys.modules[sub_path])
        
        # 2. Reload the main __init__ module to capture re-exported function pointers
        if module_path in sys.modules:
            module = importlib.reload(sys.modules[module_path])
        else:
            module = importlib.import_module(module_path)
            
        # 3. Re-bind fresh functions to registry
        for func_name in s_info.get("provided_functions", []):
            if hasattr(module, func_name):
                self.registry[func_name] = getattr(module, func_name)
                
        return True

if __name__ == "__main__":
    kernel = BorosKernel()
    import importlib
    interface_module = importlib.import_module("boros.skills.director-interface.functions.interface")
    ui = interface_module.DirectorInterface(kernel)
    ui.run()
