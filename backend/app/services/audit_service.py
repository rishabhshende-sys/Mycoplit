from sqlalchemy.orm import Session

from ..models import AuditLog


def log_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    details: str | None = None,
    user_id: int | None = 1,
) -> AuditLog:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )
    db.add(entry)
    return entry
