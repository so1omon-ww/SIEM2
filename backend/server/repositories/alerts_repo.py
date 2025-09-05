from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session
import json

SCHEMA = "security_system"

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def create_alert_for_event(session: Session, event_id: int, *, severity: str = "medium",
                           source: str = "ingest", title: Optional[str] = None, description: Optional[str] = None,
                           alert_type_id: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> int:
    sql = text(f"""
        INSERT INTO {SCHEMA}.alerts
        (event_id, agent_id, alert_type_id, ts, title, severity, source, description, acknowledged, metadata)
        SELECT e.id, e.agent_id, :alert_type_id, :ts, :title, :severity, :source, :description, FALSE, CAST(:metadata AS jsonb)
        FROM {SCHEMA}.events e WHERE e.id = :event_id
        RETURNING id
    """)
    params = {
        "event_id": int(event_id),
        "alert_type_id": alert_type_id,
        "ts": _now_utc(),
        "title": title or "Security Alert",
        "severity": severity,
        "source": source,
        "description": description or "Event triggered alert",
        "metadata": json.dumps(metadata) if metadata is not None else "{}",
    }
    rid: Result = session.execute(sql, params)
    return int(rid.scalar_one())

def get_alert(session: Session, alert_id: int) -> Optional[Dict[str, Any]]:
    row = session.execute(text(f"""
        SELECT a.id, a.ts, a.title, a.severity, a.source, a.description, a.acknowledged,
               a.acknowledged_at, a.acknowledged_by, a.event_id, a.agent_id, at.name AS alert_type, a.metadata
        FROM {SCHEMA}.alerts a
        LEFT JOIN {SCHEMA}.alert_types at ON at.id = a.alert_type_id
        WHERE a.id = :id
    """), {"id": int(alert_id)}).mappings().first()
    return dict(row) if row else None

def list_recent_alerts(session: Session, limit: int = 50) -> List[Dict[str, Any]]:
    rows = session.execute(text(f"""
        SELECT a.id, a.ts, a.title, a.severity, a.source, a.description, a.acknowledged,
               a.acknowledged_at, a.acknowledged_by, a.event_id, a.agent_id, at.name AS alert_type, a.metadata
        FROM {SCHEMA}.alerts a
        LEFT JOIN {SCHEMA}.alert_types at ON at.id = a.alert_type_id
        ORDER BY a.ts DESC
        LIMIT :limit
    """), {"limit": int(limit)}).mappings().all()
    return [dict(r) for r in rows]

def list_recent_alerts_by_owner(session: Session, owner_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    rows = session.execute(text(f"""
        SELECT a.id, a.ts, a.title, a.severity, a.source, a.description, a.acknowledged,
               a.acknowledged_at, a.acknowledged_by, a.event_id, a.agent_id, at.name AS alert_type, a.metadata
        FROM {SCHEMA}.alerts a
        LEFT JOIN {SCHEMA}.alert_types at ON at.id = a.alert_type_id
        LEFT JOIN {SCHEMA}.agents ag ON ag.id = a.agent_id
        WHERE ag.owner_id = :owner_id
        ORDER BY a.ts DESC
        LIMIT :limit
    """), {"owner_id": int(owner_id), "limit": int(limit)}).mappings().all()
    return [dict(r) for r in rows]

def acknowledge_alert(session: Session, alert_id: int, acknowledged_by: Optional[str] = None) -> bool:
    rid: Result = session.execute(text(f"""
        UPDATE {SCHEMA}.alerts 
        SET acknowledged = TRUE, acknowledged_at = :acknowledged_at, acknowledged_by = :acknowledged_by 
        WHERE id = :id 
        RETURNING id
    """), {
        "id": int(alert_id),
        "acknowledged_at": _now_utc(),
        "acknowledged_by": acknowledged_by
    })
    return rid.scalar_one_or_none() is not None
