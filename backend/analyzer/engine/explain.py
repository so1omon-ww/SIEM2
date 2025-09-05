
# explain.py - helpers to render human text for alerts
from __future__ import annotations
from typing import Dict, Any

def as_text(alert: Dict[str, Any]) -> str:
    lines = []
    lines.append(f"[{(alert.get('severity') or 'info').upper()}] {alert.get('kind','ALERT')}")
    if alert.get("title"):
        lines.append(f"Title: {alert['title']}")
    if alert.get("description"):
        lines.append(f"Description: {alert['description']}")
    ctx = alert.get("context") or {}
    if ctx:
        lines.append("Context:")
        for k, v in ctx.items():
            lines.append(f"  - {k}: {v}")
    return "\n".join(lines)
