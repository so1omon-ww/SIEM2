from datetime import datetime, timedelta
from typing import List, Dict, Any

def list_since(db, since: datetime, limit: int = 5000) -> list[dict]:
    """
    Возвращает события с ts >= since (до limit штук), как список dict.
    Требует, чтобы db был SQLAlchemy Session и таблица называлась events.
    """
    try:
        from sqlalchemy import text
    except Exception as ex:
        raise RuntimeError("SQLAlchemy is required for events_repo_adapter") from ex

    rows = db.execute(text("""
        SELECT id, ts, event_type, severity, src_ip, dst_ip, src_port, dst_port, protocol, payload
        FROM security_system.events
        WHERE ts >= :cutoff
        ORDER BY ts DESC
        LIMIT :limit
    """), {"cutoff": since, "limit": limit}).mappings().all()

    # Превращаем в чистые dict — evaluator ожидает такие поля
    out = []
    for r in rows:
        d = dict(r)
        # преобразуем ts к ISO, если это datetime (на случай сериализации)
        if hasattr(d.get("ts"), "isoformat"):
            d["ts"] = d["ts"].isoformat()
        out.append(d)
    return out
