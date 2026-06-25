from types import SimpleNamespace

from app.services.action_service import ApprovalRequired, SafetyBlock, enforce_safety
from app.services.execution_service import _ordered_nodes
from app.services.vision_service import match_template


def test_action_safety_blocks_destructive_keyword():
    workflow = SimpleNamespace(gui_actions_enabled=True, approval_required=False)
    node = SimpleNamespace(card_name="Submit payment", instruction_text="", human_approval_required=False)
    action = SimpleNamespace(action_type="click_by_coordinates", approved_for_execution=True)
    try:
        enforce_safety(workflow, node, action, {"x": 1, "y": 2, "coordinate_warning_accepted": True}, {})
    except SafetyBlock:
        return
    raise AssertionError("Expected destructive action to be blocked")


def test_gui_action_requires_workflow_enablement():
    workflow = SimpleNamespace(gui_actions_enabled=False, approval_required=False)
    node = SimpleNamespace(card_name="Read only", instruction_text="", human_approval_required=False)
    action = SimpleNamespace(action_type="click_by_image", approved_for_execution=True)
    try:
        enforce_safety(workflow, node, action, {"reference_screenshot": "x.png"}, {})
    except ApprovalRequired:
        return
    raise AssertionError("Expected GUI action approval gate")


def test_coordinate_click_requires_warning_acceptance():
    workflow = SimpleNamespace(gui_actions_enabled=True, approval_required=False)
    node = SimpleNamespace(card_name="Read only", instruction_text="", human_approval_required=False)
    action = SimpleNamespace(action_type="click_by_coordinates", approved_for_execution=True)
    try:
        enforce_safety(workflow, node, action, {"x": 1, "y": 2}, {})
    except SafetyBlock:
        return
    raise AssertionError("Expected coordinate warning block")


def test_match_template_controlled_missing_file_response():
    result = match_template("missing-current.png", "missing-reference.png")
    assert result["match_found"] is False
    assert "error" in result


def test_variable_substitution_shape():
    text = "{{customer_name}} {{from_date}}"
    context = {"customer_name": "Acme", "from_date": "2021-06-01"}
    for key, value in context.items():
        text = text.replace("{{" + key + "}}", value)
    assert text == "Acme 2021-06-01"
