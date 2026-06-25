def open_url_placeholder(url: str) -> dict:
    if not url:
        return {"ok": False, "message": "No URL configured."}
    return {"ok": True, "message": "Browser mode placeholder. URL opening is configured but login automation is disabled.", "url": url}
