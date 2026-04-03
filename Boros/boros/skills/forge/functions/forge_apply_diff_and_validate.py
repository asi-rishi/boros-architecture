import ast  
  
def forge_apply_diff_and_validate(params: dict, kernel=None) -> dict:
    """Apply a diff to a file and validate the syntax of the result."""  
    target_file = params.get("target_file")  
    replacement_chunks = params.get("replacement_chunks")  
  
    if not target_file or not replacement_chunks:  
        return {"status": "error", "message": "target_file and replacement_chunks are required."}  
  
    try:  
        with open(target_file, "r") as f:  
            content = f.read()  
  
        modified_content = content  
        for chunk in replacement_chunks:  
            modified_content = modified_content.replace(chunk["target_content"], chunk["replacement_content"], 1)  
  
        ast.parse(modified_content)  
  
        with open(target_file, "w") as f:  
            f.write(modified_content)  
  
        return {"status": "ok", "message": "Diff applied and code validated successfully."}  
    except SyntaxError as e:  
        return {"status": "error", "error_type": "SyntaxError", "message": str(e)}  
    except Exception as e:  
        return {"status": "error", "message": str(e)} 
