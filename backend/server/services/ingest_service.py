import logging
from typing import Dict, Any

from backend.server.services.event_service import save_event
from backend.analyzer.engine.evaluator import load_ruleset, on_ingest_event

LOG = logging.getLogger("ingest")

# Кеш правил анализатора
RULESET = load_ruleset()

async def ingest_event(db, event: Dict[str, Any]):
    """
    Принимает сырое событие от агента, сохраняет его и
    немедленно проверяет push-правила анализатора.

    Возвращает объект сохраненного события (как его вернул репозиторий).
    """
    db_event = await save_event(db, event)

    try:
        # push-проверка: мгновенные правила по факту поступления события
        await on_ingest_event(db_event, db, rules=RULESET)
    except Exception as e:
        LOG.warning("Analyzer on_ingest_event failed: %s", e)

    return db_event
