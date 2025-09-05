from typing import Optional, Any, List
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Header
from pydantic import BaseModel, Field, validator
import ipaddress
from ...common.db import get_session
from ..repositories.events_repo import insert_event, list_recent, list_recent_by_owner, ping_db
from ..repositories.alerts_repo import create_alert_for_event
from ...analyzer.engine.evaluator import on_ingest_event, load_ruleset

router = APIRouter()

# Кеш правил для быстрого доступа
RULESET = None

def _get_ruleset():
    """Получаем кеш правил, загружаем если нужно"""
    global RULESET
    if RULESET is None:
        try:
            RULESET = load_ruleset()
        except Exception as e:
            print(f"Failed to load ruleset: {e}")
            RULESET = []
    return RULESET

def _safe_ingest_response(event_id: int | None, alert_id: int | None):
    return {"ok": True, "event_id": event_id, "alert_id": alert_id}

def _create_portscan_alert_if_needed(session, event_id: int, payload: dict) -> int | None:
    """Создает алерт для портскана если нужно"""
    if str(payload.get("event_type", "")).startswith("net.portscan"):
        return create_alert_for_event(
            session, 
            event_id, 
            severity=payload.get("severity") or "high",
            source="rules:static",
            description=f"Port scan suspected from {payload.get('src_ip') or 'unknown'}"
        )
    return None

class EventIn(BaseModel):
    event_type: str = Field(..., description="Type of event, e.g. net.portscan.suspected")
    ts: Optional[datetime] = Field(default=None, description="Event timestamp (UTC). Defaults to now.")
    severity: Optional[str] = Field(None, description="Event severity level")
    src_ip: Optional[str] = Field(None, description="Source IP address")
    dst_ip: Optional[str] = Field(None, description="Destination IP address")
    src_port: Optional[int] = Field(None, ge=0, le=65535, description="Source port")
    dst_port: Optional[int] = Field(None, ge=0, le=65535, description="Destination port")
    protocol: Optional[str] = Field(None, description="Network protocol")
    packet_size: Optional[int] = Field(None, ge=0, description="Packet size in bytes")
    flags: Optional[str] = Field(None, description="TCP flags or other protocol flags")
    details: Optional[Any] = Field(None, description="Additional event details")
    agent_id: Optional[int] = Field(None, description="Agent ID")
    host_id: Optional[str] = Field(None, description="Host identifier")

    @validator('src_ip', 'dst_ip')
    def validate_ip(cls, v):
        if v is None:
            return v
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            raise ValueError(f'Invalid IP address: {v}')

    @validator('severity')
    def validate_severity(cls, v):
        if v is None:
            return v
        valid_severities = ['low', 'medium', 'high', 'critical', 'info', 'warning', 'error']
        if v.lower() not in valid_severities:
            raise ValueError(f'Invalid severity level: {v}. Must be one of: {valid_severities}')
        return v.lower()

    @validator('protocol')
    def validate_protocol(cls, v):
        if v is None:
            return v
        valid_protocols = ['TCP', 'UDP', 'ICMP', 'HTTP', 'HTTPS', 'DNS', 'SMTP', 'FTP']
        if v.upper() not in valid_protocols:
            # Разрешаем любые протоколы, но логируем предупреждение
            return v
        return v.upper()

@router.post("/ingest", summary="Ingest single event")
async def ingest(evt: EventIn, x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    payload = evt.model_dump()
    if payload.get("ts") is None:
        payload["ts"] = datetime.now(timezone.utc)
    
    from ..services.auth_service import get_user_id_by_api_key
    owner_id = get_user_id_by_api_key(x_api_key)
    if owner_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    with get_session() as s:
        try:
            # Находим агента пользователя
            from sqlalchemy import text
            agent_result = s.execute(text("""
                SELECT id FROM security_system.agents 
                WHERE owner_id = :owner_id
                ORDER BY created_at DESC
                LIMIT 1
            """), {"owner_id": owner_id})
            
            agent_row = agent_result.first()
            if not agent_row:
                raise HTTPException(status_code=404, detail="Agent not found for this user. Please register an agent first.")
            
            agent_id = int(agent_row[0])
            
            # Обновляем статус агента на online при получении событий
            s.execute(text("""
                UPDATE security_system.agents 
                SET status = 'online', last_seen = NOW()
                WHERE id = :agent_id
            """), {"agent_id": agent_id})
            
            # Привязываем событие к агенту
            payload["agent_id"] = agent_id
            
            # Сохраняем событие
            eid = insert_event(s, payload)
            
            # Создаем статический алерт если нужно
            aid = _create_portscan_alert_if_needed(s, eid, payload)
            
            # Применяем аналитические правила
            try:
                rules = _get_ruleset()
                if rules:
                    await on_ingest_event(payload, s, rules)
            except Exception as e:
                print(f"Analytics failed: {e}")
            
            return _safe_ingest_response(eid, aid)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ingest failed: {e}")

class EventBatchIn(BaseModel):
    items: List[EventIn]

@router.post("/ingest/batch", summary="Ingest batch of events")
async def ingest_batch(batch: EventBatchIn, x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    from ..services.auth_service import get_user_id_by_api_key
    owner_id = get_user_id_by_api_key(x_api_key)
    if owner_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    with get_session() as s:
        # Находим агента пользователя
        from sqlalchemy import text
        agent_result = s.execute(text("""
            SELECT id FROM security_system.agents 
            WHERE owner_id = :owner_id
            ORDER BY created_at DESC
            LIMIT 1
        """), {"owner_id": owner_id})
        
        agent_row = agent_result.first()
        if not agent_row:
            raise HTTPException(status_code=404, detail="Agent not found for this user. Please register an agent first.")
        
        agent_id = int(agent_row[0])
        
        # Обновляем статус агента на online при получении событий
        s.execute(text("""
            UPDATE security_system.agents 
            SET status = 'online', last_seen = NOW()
            WHERE id = :agent_id
        """), {"agent_id": agent_id})
        
        ok = 0
        last_alert_id = None
        
        for evt in batch.items:
            p = evt.model_dump()
            if p.get("ts") is None:
                p["ts"] = datetime.now(timezone.utc)
            # Привязываем событие к агенту
            p["agent_id"] = agent_id
            # Сохраняем host_id из события
            if "host_id" in p and p["host_id"]:
                p["host_id"] = p["host_id"]
            eid = insert_event(s, p)
            aid = _create_portscan_alert_if_needed(s, eid, p)
            if aid:
                last_alert_id = aid
            ok += 1
            
            # Применяем аналитические правила для каждого события
            try:
                rules = _get_ruleset()
                if rules:
                    await on_ingest_event(p, s, rules)
            except Exception as e:
                print(f"Analytics failed for event {eid}: {e}")
                
    return {"ok": True, "ingested": ok, "last_alert_id": last_alert_id}

@router.get("/recent", summary="Recent Events")
def recent_events(limit: int = Query(50, ge=1, le=500), x_api_key: str | None = Header(default=None, alias="X-API-Key")):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="X-API-Key header required")
    
    from ..services.auth_service import get_user_id_by_api_key
    uid = get_user_id_by_api_key(x_api_key)
    if uid is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    with get_session() as s:
        items = list_recent_by_owner(s, owner_id=uid, limit=limit)
        return {"items": items, "count": len(items)}

@router.post("/_ping_db", summary="Ping Db")
def ping():
    with get_session() as s:
        if ping_db(s):
            return {"ok": True}
        raise HTTPException(status_code=500, detail="DB connection failed")
