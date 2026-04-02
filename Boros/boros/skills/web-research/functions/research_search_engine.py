
def research_search_engine(params: dict, kernel=None) -> dict:
    query = params.get("query", "")
    if not query:
        return {"status": "error", "message": "query required"}
    return {"status": "ok", "message": "Web search not yet implemented. Use research_browse with a direct URL.", "query": query}
