import os

def validate_skill_syntax(skill_name: str, kernel=None) -> dict:
    """
    Validates the syntax of all Python files within a given skill.
    This is a pre-flight check before proposing a change.
    """
    if not kernel:
        return {"status": "error", "message": "Kernel not available for validation."}
    
    # Assuming forge_validate is a function available in the kernel or can be invoked
    # This is a placeholder for the actual call. In a real scenario, this would
    # likely be a direct function call or an API call to the forge skill.
    validation_result = kernel.skills["skill-forge"].functions["forge_validate"]({"skill_name": skill_name})
    
    return validation_result
