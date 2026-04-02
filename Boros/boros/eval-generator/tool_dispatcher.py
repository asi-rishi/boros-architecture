import os
import subprocess

class ToolDispatcher:
    def __init__(self, sandbox_path, kernel):
        self.sandbox_path = sandbox_path
        self.kernel = kernel
        
    def dispatch(self, tool_name, kwargs):
        try:
            # ───────────────────────────────────────────────
            # Sandbox I/O Overrides (CRITICAL FOR SAFETY)
            # ───────────────────────────────────────────────
            if tool_name == "tool_terminal":
                command = kwargs.get("command", "")
                result = subprocess.run(
                    command,
                    shell=True,
                    cwd=self.sandbox_path,
                    capture_output=True,
                    text=True
                )
                return {
                    "status": "ok",
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "returncode": result.returncode
                }
                
            elif tool_name == "tool_file_edit_diff":
                target_file = kwargs.get("target_file", "")
                # Ensure constrained strictly to sandbox
                filepath = os.path.join(self.sandbox_path, os.path.basename(target_file))
                replacement_chunks = kwargs.get("replacement_chunks", [])
                
                if not os.path.exists(filepath):
                    return {"status": "error", "message": "file not found"}
                
                with open(filepath, "r") as f:
                    content = f.read()
                    
                for chunk in replacement_chunks:
                    target = chunk.get("target_content", "")
                    replacement = chunk.get("replacement_content", "")
                    if target not in content:
                        return {"status": "error", "message": f"Target content not found in file: {target[:50]}..."}
                    content = content.replace(target, replacement, 1)

                with open(filepath, "w") as f:
                    f.write(content)
                return {"status": "ok", "message": "Patch applied successfully."}

            elif tool_name == "execute_command":
                # Original simulated subprocess
                return {"status": "ok", "stdout": "stub output", "stderr": "", "returncode": 0}
                
            elif tool_name in ("write_file", "read_file", "list_directory"):
                # Stub generic tools
                if tool_name == "write_file":
                    filepath = os.path.join(self.sandbox_path, kwargs.get("path", "temp.txt"))
                    with open(filepath, "w") as f:
                        f.write(kwargs.get("content", ""))
                    return {"status": "ok"}
                elif tool_name == "read_file":
                    filepath = os.path.join(self.sandbox_path, kwargs.get("path", "temp.txt"))
                    if not os.path.exists(filepath): return {"status": "error", "message": "not found"}
                    with open(filepath, "r") as f:
                        content = f.read()
                    return {"status": "ok", "content": content}
                elif tool_name == "list_directory":
                    return {"status": "ok", "files": os.listdir(self.sandbox_path)}

            # ───────────────────────────────────────────────
            # True Boros Capabilities
            # ───────────────────────────────────────────────
            elif tool_name in self.kernel.registry:
                return self.kernel.registry[tool_name](kwargs, self.kernel)

            return {"status": "error", "error": "unknown tool"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
