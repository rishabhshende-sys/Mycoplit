import re
from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def _keywords(text: str | None) -> list[str]:
    return [k.strip().lower() for k in (text or "").split(",") if k.strip()]


def select_workflow(db: Session, user_message: str, workflow_id: int | None = None) -> models.WorkflowTemplate | None:
    if workflow_id:
        return db.get(models.WorkflowTemplate, workflow_id)
    message = user_message.lower()
    workflows = list(db.scalars(select(models.WorkflowTemplate)).all())
    for workflow in workflows:
        if any(keyword in message for keyword in _keywords(workflow.trigger_keywords)):
            return workflow
    return workflows[0] if workflows else None


def extract_variables(user_message: str, supplied: dict[str, Any] | None = None) -> dict[str, Any]:
    variables = dict(supplied or {})
    text = user_message.strip()
    lowered = text.lower()
    if "june 2021" in lowered and ("current date" in lowered or "aaj" in lowered or "tak" in lowered):
        variables.setdefault("from_date", "2021-06-01")
        variables.setdefault("to_date", date.today().isoformat())
    code = re.search(r"(?:customer[_\s-]*code|code)[:\s]+([a-zA-Z0-9_-]+)", text, re.I)
    if code:
        variables["customer_code"] = code.group(1).upper()
    name = re.search(r"(?:customer|for|of)[:\s]+([A-Za-z][A-Za-z0-9 &.-]{2,})", text, re.I)
    if name and not variables.get("customer_name"):
        candidate = name.group(1).strip()
        candidate = re.split(r"\b(?:from|se|june|july|august|september|october|november|december|january|february|march|april|may|\d{4})\b", candidate, flags=re.I)[0].strip()
        variables["customer_name"] = candidate
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", text)
    if dates:
        variables.setdefault("from_date", dates[0])
    if len(dates) > 1:
        variables.setdefault("to_date", dates[1])
    return variables


def plan_chat_run(db: Session, user_message: str, workflow_id: int | None, variables: dict[str, Any] | None) -> dict[str, Any]:
    workflow = select_workflow(db, user_message, workflow_id)
    if not workflow:
        return {"ok": False, "message": "No workflow is available yet."}
    extracted = extract_variables(user_message, variables)
    return {"ok": True, "workflow": workflow, "variables": extracted, "message": "Workflow selected."}
