import os

class ToolDispatcher:
    def __init__(self, sandbox_path):
        self.sandbox_path = sandbox_path
        
    def dispatch(self, tool_name, kwargs):
        try:
            if tool_name == "execute_command":
                # Simulated subprocess
                return {"status": "ok", "stdout": "stub output", "stderr": "", "returncode": 0}
            elif tool_name == "write_file":
                filepath = os.path.join(self.sandbox_path, kwargs.get("path", "temp.txt"))
                with open(filepath, "w") as f:
                    f.write(kwargs.get("content", ""))
                return {"status": "ok"}
            elif tool_name == "read_file":
                filepath = os.path.join(self.sandbox_path, kwargs.get("path", "temp.txt"))
                with open(filepath, "r") as f:
                    content = f.read()
                return {"status": "ok", "content": content}
            elif tool_name == "list_directory":
                return {"status": "ok", "files": os.listdir(self.sandbox_path)}
            return {"status": "error", "error": "unknown tool"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
