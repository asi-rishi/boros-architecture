
import os, json, uuid, datetime
def evolve_create_skill(params: dict, kernel=None) -> dict:
    """Create a brand new skill with full directory structure."""
    boros_dir = os.path.join(kernel.boros_root, "boros") if kernel else "boros"
    skill_name = params.get("skill_name", "")
    description = params.get("description", "")
    functions = params.get("functions", [])

    if not skill_name:
        return {"status": "error", "message": "skill_name required"}

    skill_dir = os.path.join(boros_dir, "skills", skill_name)
    if os.path.exists(skill_dir):
        return {"status": "error", "message": f"Skill {skill_name} already exists"}

    # Create directory structure
    for subdir in ["functions", "state", "tests", "metrics", "snapshots"]:
        os.makedirs(os.path.join(skill_dir, subdir), exist_ok=True)

    # Create SKILL.md
    with open(os.path.join(skill_dir, "SKILL.md"), "w") as f:
        f.write(f"# {skill_name}\n\n{description}\n")

    # Create skill.json
    with open(os.path.join(skill_dir, "skill.json"), "w") as f:
        json.dump({"name": skill_name, "description": description, "version": "0.1.0", "provided_functions": functions}, f, indent=2)

    # Create changelog
    with open(os.path.join(skill_dir, "changelog.md"), "w") as f:
        f.write(f"# Changelog\n\n- {datetime.datetime.utcnow().isoformat()}Z: Created\n")

    # Create stub function files
    init_imports = []
    for func_name in functions:
        with open(os.path.join(skill_dir, "functions", f"{func_name}.py"), "w") as f:
            f.write(f"def {func_name}(params: dict, kernel=None) -> dict:\n    return {{'status': 'ok'}}\n")
        init_imports.append(f"from .{func_name} import {func_name}")

    with open(os.path.join(skill_dir, "functions", "__init__.py"), "w") as f:
        f.write("\n".join(init_imports) + "\n")

    return {"status": "ok", "message": f"Skill {skill_name} created with {len(functions)} functions", "path": skill_dir}
