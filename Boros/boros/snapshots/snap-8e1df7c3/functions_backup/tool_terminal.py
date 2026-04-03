import subprocess
import uuid
import threading
from ._internal.job_state import active_jobs

def tool_terminal(params: dict, kernel=None) -> dict:
    command = params.get("command")
    background = params.get("background", False)
    
    if not command: 
        return {"status": "error", "message": "No command provided."}
    
    if background:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        try:
            proc = subprocess.Popen(
                command, shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, bufsize=1
            )
            active_jobs[job_id] = proc
            return {"status": "ok", "job_id": job_id, "message": "Started in background."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    else:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
            return {
                "status": "ok", 
                "stdout": result.stdout[:4000],  # truncated to prevent extreme overfloods 
                "stderr": result.stderr[:4000], 
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Timeout expired after 120 seconds."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
