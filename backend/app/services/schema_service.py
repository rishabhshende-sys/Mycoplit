from sqlalchemy import text
from sqlalchemy.orm import Session

PHASE3_COLUMNS = {
    "workflow_templates": [
        ("gui_actions_enabled", "BOOLEAN DEFAULT 0"),
        ("approval_required", "BOOLEAN DEFAULT 1"),
    ],
    "workflow_nodes": [
        ("allow_skip_on_failure", "BOOLEAN DEFAULT 0"),
        ("human_approval_required", "BOOLEAN DEFAULT 1"),
    ],
    "card_actions": [
        ("approved_for_execution", "BOOLEAN DEFAULT 0"),
        ("requires_gui_control", "BOOLEAN DEFAULT 0"),
        ("safety_notes", "TEXT"),
    ],
    "workflow_runs": [
        ("stop_requested", "BOOLEAN DEFAULT 0"),
    ],
    "action_runs": [
        ("confidence", "FLOAT"),
        ("coordinates_json", "TEXT"),
        ("before_screenshot_path", "TEXT"),
        ("after_screenshot_path", "TEXT"),
    ],
}


def ensure_phase3_schema(db: Session) -> None:
    for table, columns in PHASE3_COLUMNS.items():
        existing = {row[1] for row in db.execute(text(f"PRAGMA table_info({table})")).all()}
        for name, ddl in columns:
            if name not in existing:
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
    db.commit()
