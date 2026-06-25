from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def now() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    role: Mapped[str] = mapped_column(String(80), default="admin")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class WorkflowTemplate(Base):
    __tablename__ = "workflow_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    trigger_keywords: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="draft")
    gui_actions_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    nodes: Mapped[list["WorkflowNode"]] = relationship(cascade="all, delete-orphan")
    edges: Mapped[list["WorkflowEdge"]] = relationship(cascade="all, delete-orphan")


class WorkflowNode(Base):
    __tablename__ = "workflow_nodes"
    __table_args__ = (Index("ix_workflow_nodes_workflow_id", "workflow_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id", ondelete="CASCADE"))
    node_type: Mapped[str] = mapped_column(String(80), nullable=False)
    card_name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instruction_text: Mapped[str | None] = mapped_column(Text)
    position_x: Mapped[float] = mapped_column(Float, default=0)
    position_y: Mapped[float] = mapped_column(Float, default=0)
    config_json: Mapped[str | None] = mapped_column(Text)
    allow_skip_on_failure: Mapped[bool] = mapped_column(Boolean, default=False)
    human_approval_required: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)

    screenshots: Mapped[list["CardScreenshot"]] = relationship(cascade="all, delete-orphan")
    actions: Mapped[list["CardAction"]] = relationship(cascade="all, delete-orphan")


class WorkflowEdge(Base):
    __tablename__ = "workflow_edges"
    __table_args__ = (Index("ix_workflow_edges_workflow_id", "workflow_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id", ondelete="CASCADE"))
    source_node_id: Mapped[int] = mapped_column(ForeignKey("workflow_nodes.id", ondelete="CASCADE"))
    target_node_id: Mapped[int] = mapped_column(ForeignKey("workflow_nodes.id", ondelete="CASCADE"))
    condition_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CardScreenshot(Base):
    __tablename__ = "card_screenshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("workflow_nodes.id", ondelete="CASCADE"))
    screenshot_type: Mapped[str] = mapped_column(String(40), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    expected_text: Mapped[str | None] = mapped_column(Text)
    crop_json: Mapped[str | None] = mapped_column(Text)
    confidence_threshold: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class CardAction(Base):
    __tablename__ = "card_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_id: Mapped[int] = mapped_column(ForeignKey("workflow_nodes.id", ondelete="CASCADE"))
    action_order: Mapped[int] = mapped_column(Integer, default=1)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    action_config_json: Mapped[str | None] = mapped_column(Text)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    approved_for_execution: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_gui_control: Mapped[bool] = mapped_column(Boolean, default=False)
    safety_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_created_at", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer)
    details: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (Index("ix_workflow_runs_workflow_status", "workflow_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflow_templates.id"))
    user_message: Mapped[str | None] = mapped_column(Text)
    input_json: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="queued")
    current_node_id: Mapped[int | None] = mapped_column(Integer)
    final_output: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    stop_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class NodeRun(Base):
    __tablename__ = "node_runs"
    __table_args__ = (Index("ix_node_runs_workflow_run_status", "workflow_run_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"))
    node_id: Mapped[int] = mapped_column(ForeignKey("workflow_nodes.id"))
    status: Mapped[str] = mapped_column(String(40), default="queued")
    input_json: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class ActionRun(Base):
    __tablename__ = "action_runs"
    __table_args__ = (Index("ix_action_runs_node_run_status", "node_run_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    node_run_id: Mapped[int] = mapped_column(ForeignKey("node_runs.id"))
    action_id: Mapped[int | None] = mapped_column(Integer)
    action_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="queued")
    input_json: Mapped[str | None] = mapped_column(Text)
    output_json: Mapped[str | None] = mapped_column(Text)
    screenshot_path: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float | None] = mapped_column(Float)
    coordinates_json: Mapped[str | None] = mapped_column(Text)
    before_screenshot_path: Mapped[str | None] = mapped_column(Text)
    after_screenshot_path: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    __table_args__ = (Index("ix_workflow_events_run_created", "workflow_run_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_run_id: Mapped[int] = mapped_column(ForeignKey("workflow_runs.id"))
    node_id: Mapped[int | None] = mapped_column(Integer)
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    original_name: Mapped[str] = mapped_column(Text, nullable=False)
    stored_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_type: Mapped[str] = mapped_column(String(40), nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(40), default="uploaded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class SalesFact(Base):
    __tablename__ = "sales_fact"
    __table_args__ = (
        Index("ix_sales_fact_customer_date", "customer_code", "invoice_date"),
        Index("ix_sales_fact_invoice_date", "invoice_date"),
        Index("ix_sales_fact_material_code", "material_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_no: Mapped[str] = mapped_column(String(120), nullable=False)
    invoice_date: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_code: Mapped[str] = mapped_column(String(120), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(Text)
    material_code: Mapped[str] = mapped_column(String(120), nullable=False)
    material_name: Mapped[str | None] = mapped_column(Text)
    quantity: Mapped[float] = mapped_column(Float, default=0)
    net_value: Mapped[float] = mapped_column(Float, default=0)
    plant: Mapped[str | None] = mapped_column(String(120))
    sales_org: Mapped[str | None] = mapped_column(String(120))
    source_file_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workflow_run_id: Mapped[int | None] = mapped_column(Integer)
    report_type: Mapped[str] = mapped_column(String(40), nullable=False)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now)
