import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

LOG = logging.getLogger("event_service")

async def save_event(db, event: Dict[str, Any]):
    """
    Сохранение события через backend.server.repositories.events_repo.
    """
    from backend.server.repositories.events_repo import insert_event

    # стандартная нормализация полей
    norm = dict(event)
    if "ts" not in norm or not norm["ts"]:
        norm["ts"] = datetime.now(timezone.utc).isoformat()

    try:
        # Вызываем insert_event напрямую
        result = insert_event(db, norm)
        LOG.debug("Event saved via repo: %s", result)
        return result
    except Exception as e:
        LOG.error("Failed to save event: %s", e)
        raise

# Добавьте импорт: from analyzer.engine.evaluator import sync_evaluate
# Затем в maybe_raise_alert: sync_evaluate(event)  # для instant rules

class EventService:
    """Сервис для работы с событиями"""
    
    def __init__(self):
        self.logger = logging.getLogger("event_service.EventService")
    
    async def save_event(self, db, event: Dict[str, Any]):
        """Сохранить событие"""
        return await save_event(db, event)
    
    async def get_event(self, event_id: int):
        """Получить событие по ID"""
        # TODO: Реализовать получение события
        pass
    
    async def list_events(self, limit: int = 100, offset: int = 0):
        """Получить список событий"""
        # TODO: Реализовать получение списка событий
        pass
