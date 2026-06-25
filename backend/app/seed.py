from sqlalchemy import select
from sqlalchemy.orm import Session

from . import models
from .services.audit_service import log_action
from .services.workflow_service import encode_json


def seed_database(db: Session) -> None:
    ensure_phase2_demo(db)
    ensure_phase3_demo(db)
    if db.scalar(select(models.User).limit(1)):
        return
    user = models.User(name="Phase 1 Admin", email="admin@mycoplit.local", role="admin")
    db.add(user)
    db.flush()
    workflow = models.WorkflowTemplate(name="Demo Visual Workflow", description="Phase 1 sample workflow with configuration-only actions.", trigger_keywords="demo, visual workflow, report", status="draft")
    db.add(workflow)
    db.flush()
    steps = [
        ("START", "START", "Workflow entry point", 0, 80),
        ("GUI Screen Step", "Open Portal Placeholder", "No external portal integration in Phase 1.", 260, 40),
        ("GUI Screen Step", "Search Customer", "Configure visual detection and text search.", 540, 40),
        ("GUI Screen Step", "Select Date Range", "Capture target state and expected success text.", 820, 40),
        ("File Step", "Download Report", "Configuration placeholder for download wait.", 1100, 40),
        ("Analysis Step", "Analyze Data", "Configuration placeholder for later AI analysis.", 1380, 40),
        ("Report Step", "Generate Report", "Configuration placeholder for PDF/Excel generation.", 1660, 40),
        ("END", "END", "Workflow completion point", 1940, 80),
    ]
    nodes = []
    for node_type, name, instruction, x, y in steps:
        node = models.WorkflowNode(workflow_id=workflow.id, node_type=node_type, card_name=name, description=instruction, instruction_text=instruction, position_x=x, position_y=y, config_json=encode_json({"mode": "read-only", "human_approval_required": False}))
        db.add(node)
        db.flush()
        nodes.append(node)
    for source, target in zip(nodes, nodes[1:]):
        db.add(models.WorkflowEdge(workflow_id=workflow.id, source_node_id=source.id, target_node_id=target.id, condition_json=encode_json({"on": "success"})))
    db.add_all([
        models.CardAction(node_id=nodes[2].id, action_order=1, action_type="click_by_text", action_config_json=encode_json({"text": "Customer ID", "execute": False}), timeout_seconds=30, retry_count=1),
        models.CardAction(node_id=nodes[4].id, action_order=1, action_type="download_wait", action_config_json=encode_json({"folder": "reports", "execute": False}), timeout_seconds=60, retry_count=2),
    ])
    log_action(db, "seed", "user", user.id, "Created sample user", user_id=user.id)
    log_action(db, "seed", "workflow", workflow.id, "Created demo visual workflow", user_id=user.id)
    db.commit()


def ensure_phase2_demo(db: Session) -> None:
    from .config import UPLOAD_DIR

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    sample = UPLOAD_DIR / "sample_sales.csv"
    if not sample.exists():
        sample.write_text(
            "invoice_no,invoice_date,customer_code,customer_name,material_code,material_name,quantity,net_value,plant,sales_org\n"
            "INV001,2021-06-05,CUST001,Acme Traders,MAT001,Widget A,10,1200,PL01,SO01\n"
            "INV002,2021-07-12,CUST001,Acme Traders,MAT002,Widget B,6,900,PL01,SO01\n"
            "INV003,2021-07-20,CUST002,Bright Retail,MAT001,Widget A,4,520,PL02,SO01\n"
            "INV004,2022-01-15,CUST001,Acme Traders,MAT003,,8,1100,PL01,SO02\n"
            "INV005,2022-03-09,CUST003,City Stores,MAT004,Widget D,3,-150,PL03,SO02\n"
            "INV006,2023-06-11,CUST001,Acme Traders,MAT001,Widget A,11,1400,PL01,SO01\n"
            "INV007,2024-02-14,CUST002,Bright Retail,MAT002,Widget B,7,980,PL02,SO01\n"
            "INV008,2025-09-24,CUST001,Acme Traders,MAT005,Widget E,5,760,PL01,SO03\n"
            "INV009,2026-01-18,CUST004,Delta Mart,MAT006,Widget F,9,1300,PL04,SO03\n"
            "INV002,2021-07-12,CUST001,Acme Traders,MAT002,Widget B,6,900,PL01,SO01\n",
            encoding="utf-8",
        )
    if db.scalar(select(models.WorkflowTemplate).where(models.WorkflowTemplate.name == "Demo File Analysis Flow")):
        db.commit()
        return
    workflow = models.WorkflowTemplate(name="Demo File Analysis Flow", description="Phase 2 sample workflow that reads, cleans, imports, analyzes, and reports on local sales data.", trigger_keywords="sales, customer, report, file analysis, sale nikal", status="active")
    db.add(workflow)
    db.flush()
    steps = [("START", "START"), ("File Step", "Select Sample CSV"), ("File Step", "Read File"), ("File Step", "Clean File"), ("Database Step", "Save To Local DB"), ("Analysis Step", "Run SQL Summary"), ("Report Step", "Generate Excel Report"), ("Report Step", "Generate PDF Report"), ("Analysis Step", "Final Answer"), ("END", "END")]
    nodes = []
    for index, (node_type, name) in enumerate(steps):
        node = models.WorkflowNode(workflow_id=workflow.id, node_type=node_type, card_name=name, description=name, instruction_text=name, position_x=index * 260, position_y=80, config_json=encode_json({"phase": 2}))
        db.add(node)
        db.flush()
        nodes.append(node)
    for source, target in zip(nodes, nodes[1:]):
        db.add(models.WorkflowEdge(workflow_id=workflow.id, source_node_id=source.id, target_node_id=target.id, condition_json=encode_json({"on": "success"})))
    actions = [(nodes[1], "wait", {"seconds": 0}), (nodes[2], "read_file", {"path": "{{uploaded_file}}"}), (nodes[3], "clean_file", {"path": "{{uploaded_file}}"}), (nodes[4], "save_to_database", {}), (nodes[5], "run_sql", {}), (nodes[6], "generate_excel", {}), (nodes[7], "generate_pdf", {}), (nodes[8], "final_answer", {})]
    for node, action_type, config in actions:
        db.add(models.CardAction(node_id=node.id, action_order=1, action_type=action_type, action_config_json=encode_json(config), timeout_seconds=60, retry_count=0))
    log_action(db, "seed", "workflow", workflow.id, "Created Demo File Analysis Flow")
    db.commit()


def ensure_phase3_demo(db: Session) -> None:
    existing = db.scalar(select(models.WorkflowTemplate).where(models.WorkflowTemplate.name == "Demo Screenshot Detection Flow"))
    if existing:
        return
    workflow = models.WorkflowTemplate(
        name="Demo Screenshot Detection Flow",
        description="Phase 3 safe GUI workflow for screenshot capture, optional image matching, approval pause, and final answer.",
        trigger_keywords="screenshot, image match, gui detection, screen test",
        status="active",
        gui_actions_enabled=False,
        approval_required=True,
    )
    db.add(workflow)
    db.flush()
    steps = [("START", "START"), ("GUI Screen Step", "Take Screenshot"), ("GUI Screen Step", "Wait For Image Placeholder"), ("Human Approval Step", "Human Approval"), ("Analysis Step", "Final Answer"), ("END", "END")]
    nodes = []
    for index, (node_type, name) in enumerate(steps):
        node = models.WorkflowNode(
            workflow_id=workflow.id,
            node_type=node_type,
            card_name=name,
            description=name,
            instruction_text="Safe Phase 3 demo step. No login or destructive external action is allowed.",
            position_x=index * 260,
            position_y=180,
            config_json=encode_json({"phase": 3}),
            human_approval_required=True,
            allow_skip_on_failure=True,
        )
        db.add(node)
        db.flush()
        nodes.append(node)
    for source, target in zip(nodes, nodes[1:]):
        db.add(models.WorkflowEdge(workflow_id=workflow.id, source_node_id=source.id, target_node_id=target.id, condition_json=encode_json({"on": "success"})))
    actions = [
        (nodes[1], "take_screenshot", {"approved_once": True}, True),
        (nodes[2], "wait_for_image", {"reference_screenshot": "", "confidence_threshold": 0.8}, False),
        (nodes[3], "human_approval", {}, False),
        (nodes[4], "final_answer", {}, True),
    ]
    for node, action_type, config, approved in actions:
        db.add(models.CardAction(
            node_id=node.id,
            action_order=1,
            action_type=action_type,
            action_config_json=encode_json(config),
            timeout_seconds=30,
            retry_count=0,
            approved_for_execution=approved,
            requires_gui_control=action_type in {"take_screenshot", "wait_for_image"},
            safety_notes="Phase 3 approval-first demo action.",
        ))
    log_action(db, "seed", "workflow", workflow.id, "Created Demo Screenshot Detection Flow")
    db.commit()

