from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowBase(BaseModel):
    name: str
    description: str | None = None
    trigger_keywords: str | None = None
    status: str = "draft"
    gui_actions_enabled: bool = False
    approval_required: bool = True


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    trigger_keywords: str | None = None
    status: str | None = None
    gui_actions_enabled: bool | None = None
    approval_required: bool | None = None


class NodeBase(BaseModel):
    node_type: str
    card_name: str
    description: str | None = None
    instruction_text: str | None = None
    position_x: float = 0
    position_y: float = 0
    config_json: dict[str, Any] | None = Field(default_factory=dict)
    allow_skip_on_failure: bool = False
    human_approval_required: bool = True


class NodeCreate(NodeBase):
    pass


class NodeUpdate(BaseModel):
    node_type: str | None = None
    card_name: str | None = None
    description: str | None = None
    instruction_text: str | None = None
    position_x: float | None = None
    position_y: float | None = None
    config_json: dict[str, Any] | None = None
    allow_skip_on_failure: bool | None = None
    human_approval_required: bool | None = None


class EdgeCreate(BaseModel):
    source_node_id: int
    target_node_id: int
    condition_json: dict[str, Any] | None = Field(default_factory=dict)


class ScreenshotCreate(BaseModel):
    screenshot_type: str
    description: str | None = None
    expected_text: str | None = None
    crop_json: dict[str, Any] | None = Field(default_factory=dict)
    confidence_threshold: float = 0.8


class ActionCreate(BaseModel):
    action_order: int = 1
    action_type: str
    action_config_json: dict[str, Any] | None = Field(default_factory=dict)
    timeout_seconds: int = 30
    retry_count: int = 0
    approved_for_execution: bool = False
    requires_gui_control: bool = False
    safety_notes: str | None = None


class ActionUpdate(BaseModel):
    action_order: int | None = None
    action_type: str | None = None
    action_config_json: dict[str, Any] | None = None
    timeout_seconds: int | None = None
    retry_count: int | None = None
    approved_for_execution: bool | None = None
    requires_gui_control: bool | None = None
    safety_notes: str | None = None


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CardActionOut(ORMModel):
    id: int
    node_id: int
    action_order: int
    action_type: str
    action_config_json: dict[str, Any] | None
    timeout_seconds: int
    retry_count: int
    approved_for_execution: bool = False
    requires_gui_control: bool = False
    safety_notes: str | None = None
    created_at: datetime


class CardScreenshotOut(ORMModel):
    id: int
    node_id: int
    screenshot_type: str
    file_path: str
    description: str | None
    expected_text: str | None
    crop_json: dict[str, Any] | None
    confidence_threshold: float
    created_at: datetime


class WorkflowNodeOut(ORMModel):
    id: int
    workflow_id: int
    node_type: str
    card_name: str
    description: str | None
    instruction_text: str | None
    position_x: float
    position_y: float
    config_json: dict[str, Any] | None
    allow_skip_on_failure: bool = False
    human_approval_required: bool = True
    created_at: datetime
    updated_at: datetime
    screenshots: list[CardScreenshotOut] = []
    actions: list[CardActionOut] = []


class WorkflowEdgeOut(ORMModel):
    id: int
    workflow_id: int
    source_node_id: int
    target_node_id: int
    condition_json: dict[str, Any] | None
    created_at: datetime


class WorkflowOut(ORMModel):
    id: int
    name: str
    description: str | None
    trigger_keywords: str | None
    status: str
    gui_actions_enabled: bool = False
    approval_required: bool = True
    created_at: datetime
    updated_at: datetime
    nodes: list[WorkflowNodeOut] = []
    edges: list[WorkflowEdgeOut] = []


class AuditLogOut(ORMModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details: str | None
    created_at: datetime


class DashboardStats(BaseModel):
    total_workflows: int
    total_cards: int
    uploaded_screenshots: int
    recent_workflows: list[WorkflowOut]
    recent_audit_logs: list[AuditLogOut]
