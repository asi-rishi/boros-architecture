
def router_get_tools(params: dict, kernel=None) -> dict:
    """Return all available tool names and descriptions."""
    if kernel:
        tools = list(kernel.registry.keys())
        return {"status": "ok", "tools": tools, "count": len(tools)}
    return {"status": "ok", "tools": [], "count": 0}
