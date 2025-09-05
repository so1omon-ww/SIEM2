from __future__ import annotations
import json
import logging
from typing import Any, Optional
from sqlalchemy import text

LOG = logging.getLogger("alert_service")

def _event_to_dict(ev: Any) -> dict:
    """Преобразуем любое событие в dict (dict / Pydantic / ORM / RowMapping)."""
    if ev is None:
        return {}
    if isinstance(ev, dict):
        return ev
    # Pydantic v2
    if hasattr(ev, "model_dump"):
        try:
            return ev.model_dump()  # type: ignore
        except Exception:
            pass
    # Pydantic v1
    if hasattr(ev, "dict"):
        try:
            return ev.dict()  # type: ignore
        except Exception:
            pass
    # SQLAlchemy ORM instance (у него обычно есть __dict__ с внутренними полями)
    try:
        d = {k: v for k, v in vars(ev).items() if not k.startswith("_")}
        if d:
            return d
    except Exception:
        pass
    # Row / RowMapping
    if hasattr(ev, "_mapping"):
        try:
            return dict(ev._mapping)  # type: ignore
        except Exception:
            pass
    if hasattr(ev, "keys") and hasattr(ev, "__getitem__"):
        try:
            return {k: ev[k] for k in ev.keys()}
        except Exception:
            pass
    return {}

def _get_or_create_alert_type(db, name: str, description: str = "") -> int:
    row = db.execute(
        text("SELECT id FROM security_system.alert_types WHERE name=:n"),
        {"n": name},
    ).fetchone()
    if row and row[0]:
        return int(row[0])

    row = db.execute(
        text("""
            INSERT INTO security_system.alert_types(name, description)
            VALUES (:n, :d)
            ON CONFLICT (name) DO UPDATE SET description=EXCLUDED.description
            RETURNING id
        """),
        {"n": name, "d": description},
    ).fetchone()
    db.commit()
    return int(row[0])

async def raise_alert(
    db,
    *,
    source: str,
    severity: str,
    title: str,
    description: str,
    event_id: Optional[int] = None,
    agent_id: Optional[int] = None,
    context: Optional[dict] = None,
    dedup_key: Optional[str] = None,
) -> int:
    """Создать алёрт указанного типа."""
    at_id = _get_or_create_alert_type(db, source, description)
    payload_json = json.dumps(context or {}, default=str)

    row = db.execute(
        text("""
            INSERT INTO security_system.alerts
            (event_id, agent_id, alert_type_id, ts, title, severity, source, description, acknowledged, metadata)
            VALUES (:event_id, :agent_id, :at_id, NOW(), :title, :sev, :src, :desc, FALSE, CAST(:meta AS jsonb))
            RETURNING id
        """),
        {
            "event_id": event_id,
            "agent_id": agent_id,
            "at_id": at_id,
            "title": title,
            "sev": severity,
            "src": source,
            "desc": description,
            "meta": payload_json,
        },
    ).fetchone()
    db.commit()
    return int(row[0])

def maybe_raise_alert(db, event, payload=None):
    """
    Базовая синхронная логика: из события 'net.portscan.suspected' поднимаем PORT_SCAN.
    Возвращает id алёрта или None.
    """
    e = _event_to_dict(event)

    # Если payload передали аргументом → добавим в e
    if payload and "payload" not in e:
        e["payload"] = payload

    et = e.get("event_type") or e.get("type")
    if et == "net.portscan.suspected":
        src_ip = e.get("src_ip")
        if not src_ip:
            payload = e.get("payload") or {}
            src_ip = payload.get("src_ip")
        desc = f"Port scan suspected from {src_ip}" if src_ip else "Port scan suspected"
        meta = {"event_type": et, "src_ip": src_ip, "payload": e.get("payload")}
        try:
            return raise_alert(
                db,
                event_id=e.get("id"),
                agent_id=e.get("agent_id"),
                source="rules:push",
                severity="high",
                title="Port Scan Detected",
                description=desc,
                context=meta,
            )
        except Exception as ex:
            LOG.warning("raise_alert failed: %s", ex)
            return None
    return None


class AlertService:
    """Сервис для работы с алертами"""
    
    def __init__(self):
        self.logger = logging.getLogger("alert_service.AlertService")
    
    async def raise_alert(
        self,
        db,
        *,
        source: str,
        severity: str,
        title: str,
        description: str,
        event_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        context: Optional[dict] = None,
        dedup_key: Optional[str] = None,
    ) -> int:
        """Создать алерт"""
        return await raise_alert(
            db,
            source=source,
            severity=severity,
            title=title,
            description=description,
            event_id=event_id,
            agent_id=agent_id,
            context=context,
            dedup_key=dedup_key
        )
    
    async def get_alert(self, alert_id: int):
        """Получить алерт по ID"""
        # TODO: Реализовать получение алерта
        pass
    
    async def list_alerts(self, limit: int = 100, offset: int = 0):
        """Получить список алертов"""
        # TODO: Реализовать получение списка алертов
        pass


__all__ = ["maybe_raise_alert", "raise_alert"]
