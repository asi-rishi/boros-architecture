import os

def tool_file_edit_diff(params: dict, kernel=None) -> dict:
    target_file = params.get("target_file")
    replacement_chunks = params.get("replacement_chunks", [])
    
    if not target_file: return {"status": "error", "message": "target_file required"}
    if not os.path.exists(target_file): return {"status": "error", "message": "file not found"}
    
    try:
        with open(target_file, "r") as f:
            content = f.read()
            
        for chunk in replacement_chunks:
            target = chunk.get("target_content", "")
            replacement = chunk.get("replacement_content", "")
            if target not in content:
                return {"status": "error", "message": f"Target content not found in file: {target[:50]}..."}
            content = content.replace(target, replacement, 1)

        with open(target_file, "w") as f:
            f.write(content)
            
        return {"status": "ok", "message": "Patch applied successfully."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
