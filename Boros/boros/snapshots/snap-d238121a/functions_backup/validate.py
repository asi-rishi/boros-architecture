import ast  
  
def validate_code_changes(code_string: str, kernel=None) -> dict:
    """Validate a string of Python code for syntax errors using ast.parse."""  
    try:  
        ast.parse(code_string)  
        return {"status": "ok", "message": "Code is syntactically valid."}  
    except SyntaxError as e:  
        return {"status": "error", "error_type": "SyntaxError", "message": str(e)} 
