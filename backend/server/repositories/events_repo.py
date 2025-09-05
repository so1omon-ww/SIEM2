from typing import Any, Dict, List
from datetime import datetime, timezone
from sqlalchemy import text
from sqlalchemy.engine import Result
from sqlalchemy.orm import Session
import json
import ipaddress

SCHEMA = "security_system"

def ping_db(session: Session) -> bool:
    r: Result = session.execute(text("SELECT 1"))
    return r.scalar_one() == 1

def _validate_ip(ip_str: str) -> bool:
    """Валидация IP адреса"""
    if not ip_str:
        return True
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

def _validate_port(port: Any) -> int | None:
    """Валидация порта"""
    if port is None:
        return None
    try:
        port_int = int(port)
        if 0 <= port_int <= 65535:
            return port_int
        return None
    except (ValueError, TypeError):
        return None

def insert_event(session: Session, payload: Dict[str, Any]) -> int:
    p = {k: payload.get(k) for k in (
        "agent_id","host_id","ts","event_type","severity","src_ip","dst_ip","src_port",
        "dst_port","protocol","packet_size","flags","details"
    )}
    
    # Валидация и нормализация данных
    if not p.get("ts"):
        p["ts"] = datetime.now(timezone.utc)
    
    # Валидация IP адресов
    if p.get("src_ip") and not _validate_ip(p["src_ip"]):
        p["src_ip"] = None
    if p.get("dst_ip") and not _validate_ip(p["dst_ip"]):
        p["dst_ip"] = None
    
    # Валидация портов
    p["src_port"] = _validate_port(p.get("src_port"))
    p["dst_port"] = _validate_port(p.get("dst_port"))
    
    # Валидация packet_size
    if p.get("packet_size") is not None:
        try:
            p["packet_size"] = int(p["packet_size"])
            if p["packet_size"] < 0:
                p["packet_size"] = None
        except (ValueError, TypeError):
            p["packet_size"] = None
    
    # Обработка details как JSONB
    if isinstance(p.get("details"), (dict, list)):
        p["details"] = json.dumps(p["details"], ensure_ascii=False)
    elif p.get("details") is not None:
        p["details"] = json.dumps({"raw": str(p["details"])}, ensure_ascii=False)
    else:
        p["details"] = "{}"
    
    sql = text(f"""
        INSERT INTO {SCHEMA}.events
        (agent_id, host_id, ts, event_type, severity, src_ip, dst_ip, src_port, dst_port,
         protocol, packet_size, flags, details)
        VALUES (:agent_id, :host_id, :ts, :event_type, :severity, :src_ip, :dst_ip, :src_port, :dst_port,
                :protocol, :packet_size, :flags, :details)
        RETURNING id
    """)
    rid: Result = session.execute(sql, p)
    return int(rid.scalar_one())

def list_recent(session: Session, limit: int = 50) -> List[Dict[str, Any]]:
    rows = session.execute(text(f"""
        SELECT id, agent_id, host_id, ts, event_type, severity, src_ip, dst_ip, src_port, dst_port,
               protocol, packet_size, flags, details
        FROM {SCHEMA}.events
        ORDER BY ts DESC
        LIMIT :limit
    """), {"limit": int(limit)}).mappings().all()
    return [dict(r) for r in rows]

def list_recent_by_owner(session: Session, owner_id: int, limit: int = 50) -> List[Dict[str, Any]]:
    rows = session.execute(text(f"""
        SELECT e.id, e.agent_id, e.host_id, e.ts, e.event_type, e.severity, e.src_ip, e.dst_ip, e.src_port, e.dst_port,
               e.protocol, e.packet_size, e.flags, e.details
        FROM {SCHEMA}.events e
        LEFT JOIN {SCHEMA}.agents ag ON ag.id = e.agent_id
        WHERE ag.owner_id = :owner_id
        ORDER BY e.ts DESC
        LIMIT :limit
    """), {"owner_id": int(owner_id), "limit": int(limit)}).mappings().all()
    return [dict(r) for r in rows]