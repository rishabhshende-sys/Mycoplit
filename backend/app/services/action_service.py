import time
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .. import models
from .file_service import clean_file, inspect_file, save_sales_to_database
from .report_service import generate_excel, generate_pdf
from .sales_service import run_sales_summary
from .vision_service import detect_text, match_template, take_current_screenshot, wait_for_image, wait_for_text
from .workflow_service import decode_json

GUI_ACTIONS = {
    "click_by_image", "click_by_text", "click_by_coordinates", "type_text", "press_key", "hotkey", "scroll",
    "wait_for_image", "wait_for_text", "take_screenshot", "extract_text",
}
DESTRUCTIVE_KEYWORDS = ["delete", "remove", "submit", "post", "approve", "reject", "cancel", "transfer", "payment", "save changes", "update record"]
PASSWORD_KEYWORDS = ["password", "passwd", "passcode", "otp", "mfa", "captcha", "secret"]


class SafetyBlock(Exception):
    pass


class ApprovalRequired(Exception):
    pass


def is_gui_action(action_type: str) -> bool:
    return action_type in GUI_ACTIONS


def _config(action: models.CardAction, context: dict[str, Any]) -> dict[str, Any]:
    raw = decode_json(action.action_config_json) or {}
    output = {}
    for key, value in raw.items():
        if isinstance(value, str):
            for ctx_key, replacement in context.items():
                value = value.replace("{{" + ctx_key + "}}", str(replacement))
        output[key] = value
    return output


def _has_dangerous_text(*values: Any) -> str | None:
    text = " ".join(str(v).lower() for v in values if v is not None)
    for keyword in DESTRUCTIVE_KEYWORDS:
        if keyword in text:
            return keyword
    return None


def _looks_password_like(*values: Any) -> bool:
    text = " ".join(str(v).lower() for v in values if v is not None)
    return any(keyword in text for keyword in PASSWORD_KEYWORDS)


def enforce_safety(workflow: models.WorkflowTemplate, node: models.WorkflowNode, action: models.CardAction, config: dict[str, Any], context: dict[str, Any] | None = None) -> None:
    if _has_dangerous_text(action.action_type, node.card_name, node.instruction_text, config):
        raise SafetyBlock("Destructive external action blocked by Phase 3 read-only safety policy.")
    if _looks_password_like(action.action_type, node.card_name, node.instruction_text, config):
        raise SafetyBlock("Password, MFA, OTP, or CAPTCHA automation is blocked.")
    if action.action_type == "click_by_coordinates" and not config.get("coordinate_warning_accepted"):
        raise SafetyBlock("Coordinate click blocked until coordinate_warning_accepted is true.")
    if is_gui_action(action.action_type):
        if not workflow.gui_actions_enabled:
            raise ApprovalRequired("GUI action requires workflow gui_actions_enabled=true.")
        if not action.approved_for_execution:
            raise ApprovalRequired("GUI action requires approved_for_execution=true.")
        if workflow.approval_required or node.human_approval_required:
            approved_once = config.get("approved_once") or (context or {}).get("_approved_once")
            if not approved_once:
                raise ApprovalRequired("GUI action is waiting for human approval.")


def execute_action(db: Session, workflow: models.WorkflowTemplate, run: models.WorkflowRun, node: models.WorkflowNode, action: models.CardAction, context: dict[str, Any]) -> dict[str, Any]:
    config = _config(action, context)
    enforce_safety(workflow, node, action, config, context)
    action_type = action.action_type
    if action_type == "wait":
        seconds = min(float(config.get("seconds", 1)), 10)
        time.sleep(seconds)
        return {"waited_seconds": seconds}
    if action_type == "human_approval":
        raise ApprovalRequired("Human approval is required before continuing.")
    if action_type == "take_screenshot":
        return take_current_screenshot()
    if action_type == "wait_for_image":
        ref = config.get("reference_screenshot") or config.get("path")
        if not ref:
            raise SafetyBlock("wait_for_image requires reference_screenshot.")
        return wait_for_image(str(ref), int(config.get("timeout", action.timeout_seconds)), float(config.get("confidence_threshold", 0.8)))
    if action_type == "click_by_image":
        ref = config.get("reference_screenshot") or config.get("path")
        if not ref:
            raise SafetyBlock("click_by_image requires reference_screenshot.")
        before = take_current_screenshot()
        match = match_template(before["path"], str(ref))
        if not match.get("match_found") and match.get("confidence", 0) < float(config.get("confidence_threshold", 0.8)):
            raise SafetyBlock(f"Image match confidence too low: {match.get('confidence', 0)}")
        from ..tools.mouse_keyboard_tools import click
        click(int(match["center_x"]), int(match["center_y"]))
        after = take_current_screenshot()
        return {"before_screenshot_path": before["path"], "after_screenshot_path": after["path"], **match}
    if action_type == "click_by_text":
        shot = take_current_screenshot()
        result = detect_text(shot["path"], str(config.get("expected_text") or config.get("text") or ""))
        if result.get("error"):
            raise SafetyBlock(result["error"])
        raise SafetyBlock("OCR text click requires bounding boxes; OCR location is not configured in MVP.")
    if action_type == "click_by_coordinates":
        from ..tools.mouse_keyboard_tools import click
        x, y = int(config.get("x", 0)), int(config.get("y", 0))
        before = take_current_screenshot()
        click(x, y)
        after = take_current_screenshot()
        return {"coordinates": {"x": x, "y": y}, "before_screenshot_path": before["path"], "after_screenshot_path": after["path"], "warning": "Coordinate clicks are fragile."}
    if action_type == "type_text":
        text = str(config.get("text", ""))
        if _looks_password_like(text):
            raise SafetyBlock("Password-like text typing is blocked.")
        from ..tools.mouse_keyboard_tools import type_text
        type_text(text)
        return {"typed_chars": len(text)}
    if action_type == "press_key":
        from ..tools.mouse_keyboard_tools import press_key
        key = str(config.get("key", "enter"))
        press_key(key)
        return {"key": key}
    if action_type == "hotkey":
        from ..tools.mouse_keyboard_tools import hotkey
        keys = config.get("keys") or []
        if isinstance(keys, str):
            keys = [k.strip() for k in keys.split("+")]
        hotkey(keys)
        return {"keys": keys}
    if action_type == "scroll":
        from ..tools.mouse_keyboard_tools import scroll
        amount = int(config.get("amount", -5))
        scroll(amount)
        return {"amount": amount}
    if action_type == "wait_for_text":
        return wait_for_text(str(config.get("expected_text") or config.get("text") or ""), int(config.get("timeout", action.timeout_seconds)))
    if action_type == "extract_text":
        shot_path = config.get("path")
        if not shot_path:
            shot_path = take_current_screenshot()["path"]
        result = detect_text(str(shot_path))
        if result.get("error"):
            raise SafetyBlock(result["error"])
        return result
    if action_type == "download_wait":
        folder = Path(str(config.get("folder") or Path.home() / "Downloads"))
        before = {p.name for p in folder.glob("*")} if folder.exists() else set()
        deadline = time.time() + int(config.get("timeout", action.timeout_seconds))
        while time.time() < deadline:
            if not folder.exists():
                time.sleep(0.5)
                continue
            for path in folder.glob("*"):
                if path.name not in before and path.stat().st_size > 0 and path.suffix.lower() not in {".tmp", ".crdownload", ".part"}:
                    context["downloaded_file"] = str(path)
                    return {"downloaded_file": str(path)}
            time.sleep(0.8)
        raise SafetyBlock("download_wait timed out without a completed file.")
    if action_type == "read_file":
        file_path = config.get("path") or context.get("uploaded_file")
        return {"file_path": file_path, **inspect_file(file_path)}
    if action_type == "clean_file":
        file_path = config.get("path") or context.get("uploaded_file") or context.get("last_output", {}).get("file_path")
        result = clean_file(file_path)
        context["cleaned_file"] = result["cleaned_file"]
        return result
    if action_type == "save_to_database":
        return save_sales_to_database(db, config.get("path") or context.get("cleaned_file"), context.get("source_file_id"))
    if action_type == "run_sql":
        summary = run_sales_summary(db, context)
        context["analysis"] = summary
        return summary
    if action_type == "generate_excel":
        report = generate_excel(db, run.id, context.get("analysis") or context.get("last_output") or {})
        context.setdefault("reports", []).append(report)
        context["report_path"] = report["file_path"]
        return report
    if action_type == "generate_pdf":
        report = generate_pdf(db, run.id, context.get("analysis") or context.get("last_output") or {})
        context.setdefault("reports", []).append(report)
        context["report_path"] = report["file_path"]
        return report
    if action_type == "final_answer":
        from ..agents.final_answer_agent import build_final_answer
        final = build_final_answer(context.get("analysis") or {}, context.get("reports", []))
        context["final_answer"] = final
        return final
    return {"message": f"Unsupported action type {action_type} skipped safely."}


