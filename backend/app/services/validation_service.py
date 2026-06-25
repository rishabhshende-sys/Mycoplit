def validate_required_variables(variables, required):
    missing = [name for name in required if not variables.get(name)]
    return {"verified": not missing, "partial": bool(missing), "failed": False, "missing": missing}
