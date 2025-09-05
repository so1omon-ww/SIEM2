
# evaluator.py - load YAML rules and evaluate them (immediate/threshold)
from __future__ import annotations
import asyncio, os, re, json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    import yaml  # PyYAML
except Exception as e:
    raise RuntimeError("PyYAML is required for analyzer: pip install PyYAML") from e

BASE = Path(__file__).resolve().parents[2]  # .../backend
ANALYZER_DIR = BASE / "analyzer"
RULES_DIR = ANALYZER_DIR / "rules" / "builtin"
STATE_DIR = ANALYZER_DIR / ".state"
STATE_FILE = STATE_DIR / "state.json"

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _parse_window(s: str) -> timedelta:
    s = s.strip().lower()
    m = re.fullmatch(r"(\d+)\s*([smhd])", s)
    if not m:
        raise ValueError(f"Bad window format: {s}")
    n = int(m.group(1)); u = m.group(2)
    return {"s": timedelta(seconds=n), "m": timedelta(minutes=n),
            "h": timedelta(hours=n), "d": timedelta(days=n)}[u]

def _load_state() -> Dict[str, Any]:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"last_processed_id": {}, "rules_hash": {}}

def _save_state(st: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")

def _hash_rule(d: Dict[str, Any]) -> str:
    return json.dumps(d, sort_keys=True, ensure_ascii=False)

@dataclass
class Rule:
    name: str
    type: str  # "immediate" | "threshold"
    match: Dict[str, Any] = field(default_factory=dict)
    severity: str = "info"
    title: str = ""
    description: Optional[str] = None
    dedup: Optional[str] = None
    group_by: Optional[str] = None
    window: Optional[str] = None
    threshold: Optional[int] = None
    context_fields: List[str] = field(default_factory=list)

def _load_yaml_rules(path: Path) -> List[Rule]:
    rules: List[Rule] = []
    for f in sorted(path.glob("*.yaml")):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        items = data["rules"] if isinstance(data, dict) and "rules" in data else [data]
        for it in items:
            rules.append(Rule(
                name=it["name"], type=it["type"], match=it.get("match", {}) or {},
                severity=it.get("severity", "info"), title=it.get("title",""),
                description=it.get("description"), dedup=it.get("dedup"),
                group_by=it.get("group_by"), window=it.get("window"),
                threshold=it.get("threshold"), context_fields=it.get("context_fields", [])
            ))
    return rules

def load_ruleset() -> List[Rule]:
    rules = _load_yaml_rules(RULES_DIR)
    st = _load_state()
    st["rules_hash"] = {r.name: _hash_rule(r.__dict__) for r in rules}
    _save_state(st)
    return rules

def get_field(event: Any, key: str) -> Any:
    if "." in key:
        head, tail = key.split(".", 1)
        base = getattr(event, head, None) if hasattr(event, head) else (event.get(head) if isinstance(event, dict) else None)
        if base is None:
            return None
        if hasattr(base, tail): return getattr(base, tail)
        if isinstance(base, dict): return base.get(tail)
        return None
    else:
        if hasattr(event, key): return getattr(event, key)
        if isinstance(event, dict): return event.get(key)
        return None

def match_event(event: Any, m: Dict[str, Any]) -> bool:
    for k, v in m.items():
        val = get_field(event, k)
        if isinstance(v, list):
            if val not in v: return False
        elif isinstance(v, str) and v.startswith("re:"):
            pat = v[3:]
            if not isinstance(val, str) or not re.search(pat, val or ""): return False
        else:
            if val != v: return False
    return True

def format_text(tpl: str, event: Any, extra: Dict[str, Any] | None = None) -> str:
    ctx = {}
    if isinstance(event, dict): ctx.update(event)
    else: ctx.update(getattr(event, "__dict__", {}) or {})
    # Используем details вместо payload, так как в БД поле называется details
    pl = get_field(event, "details")
    if isinstance(pl, dict): ctx.update(pl)
    if extra: ctx.update(extra)
    try: return tpl.format(**ctx)
    except Exception: return tpl

async def _raise_alert(db, *, kind: str, severity: str,
                       title: str | None = None,
                       description: str | None = None,
                       dedup_key: str | None = None,
                       context: Dict[str, Any] | None = None,
                       agent_id: Any = None, event_id: Any = None):
    try:
        from ...server.services.alert_service import raise_alert as srv_raise_alert

        await srv_raise_alert(
            db,  # db как первый позиционный аргумент
            source=kind,
            severity=severity,
            # если title пуст — используем имя правила
            title=title or kind,
            description=description,
            context=context,
            agent_id=agent_id,
            event_id=event_id,
            dedup_key=dedup_key
        )
    except Exception as e:
        raise

async def on_ingest_event(event: Any, db, rules: List[Rule] | None = None) -> int:
    if rules is None:
        rules = load_ruleset()
    created = 0
    for r in rules:
        if r.type != "immediate": continue
        if match_event(event, r.match):
            title = format_text(r.title or r.name, event)
            dedup_key = format_text(r.dedup or "", event) if r.dedup else None
            ctx = {"rule": r.name}
            # Используем details вместо payload, так как в БД поле называется details
            pl = getattr(event, "details", None) or (event.get("details") if isinstance(event, dict) else None) or {}
            if isinstance(pl, dict):
                for f in r.context_fields:
                    if f in pl: ctx[f] = pl[f]
            await _raise_alert(db, kind=r.name, severity=r.severity, title=title,
                               description=r.description, dedup_key=dedup_key,
                               context=ctx,
                               agent_id=getattr(event, "agent_id", None) or (event.get("agent_id") if isinstance(event, dict) else None),
                               event_id=getattr(event, "id", None) or (event.get("id") if isinstance(event, dict) else None))
            created += 1
    return created

async def evaluate_window(db, rules: List[Rule], events: Iterable[Any], window_until: datetime | None = None) -> int:
    created = 0
    events = list(events)
    by_type: Dict[str, List[Any]] = {}
    for ev in events:
        t = getattr(ev, "event_type", None) or (ev.get("event_type") if isinstance(ev, dict) else None)
        by_type.setdefault(t, []).append(ev)

    for r in rules:
        if r.type != "threshold": continue
        if not r.window or not r.threshold or not r.group_by: continue
        subset = by_type.get(r.match.get("event_type"), []) if r.match.get("event_type") else events
        subset = [ev for ev in subset if match_event(ev, r.match)]
        buckets: Dict[str, List[Any]] = {}
        for ev in subset:
            key = get_field(ev, r.group_by)
            if key is None: continue
            buckets.setdefault(str(key), []).append(ev)
        for group, items in buckets.items():
            if len(items) >= int(r.threshold):
                ctx = {"rule": r.name, "group": group, "count": len(items)}
                sample = items[-1]
                # Используем details вместо payload, так как в БД поле называется details
                pl = getattr(sample, "details", None) or (sample.get("details") if isinstance(sample, dict) else None) or {}
                if isinstance(pl, dict):
                    for f in r.context_fields:
                        if f in pl: ctx[f] = pl[f]
                title = (r.title or r.name).replace("{group}", str(group)).replace("{count}", str(len(items)))
                dedup_key = (r.dedup or "").replace("{group}", str(group)) if r.dedup else None
                agent_id = getattr(sample, "agent_id", None) or (sample.get("agent_id") if isinstance(sample, dict) else None)
                event_id = getattr(sample, "id", None) or (sample.get("id") if isinstance(sample, dict) else None)
                await _raise_alert(db, kind=r.name, severity=r.severity, title=title,
                                   description=r.description, dedup_key=dedup_key,
                                   context=ctx, agent_id=agent_id, event_id=event_id)
                created += 1
    return created

def _fetch_recent_events(db, minutes: int = 15, limit: int = 5000):
    """Загружаем свежие события за N минут."""
    try:
        from sqlalchemy.sql import text
        minutes = int(minutes)
        limit = int(limit)
        q = text(f"""
            SELECT id, ts, event_type, severity, agent_id,
                   src_ip, dst_ip, src_port, dst_port, protocol,
                   packet_size, flags, details
            FROM security_system.events
            WHERE ts >= NOW() - INTERVAL '{minutes} minutes'
            ORDER BY ts DESC
            LIMIT :lim
        """)
        rows = db.execute(q, {"lim": limit}).mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        import logging
        logging.getLogger("analyzer.evaluator").warning("fetch_recent_events failed: %s", e)
        return []

def evaluate_window_sync(db, rules, events=None):
    """
    Синхронная версия evaluate_window для совместимости.
    """
    if events is None:
        events = _fetch_recent_events(db, minutes=15)
    
    # Создаем асинхронную задачу
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Если уже в цикле событий, создаем задачу
            task = asyncio.create_task(evaluate_window(db, rules, events))
            return task
        else:
            # Если нет цикла событий, запускаем новый
            return asyncio.run(evaluate_window(db, rules, events))
    except RuntimeError:
        # Если нет цикла событий, создаем новый
        return asyncio.run(evaluate_window(db, rules, events))

