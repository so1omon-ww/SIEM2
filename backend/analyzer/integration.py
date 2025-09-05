"""
Интеграция нового анализатора с существующей системой SIEM
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .engine.analyzer_core import AnalyzerCore
from .config import AnalyzerConfig
from backend.common.db import get_session
from backend.server.services.event_service import EventService
from backend.server.services.alert_service import AlertService


class AnalyzerIntegration:
    """Интеграция анализатора с существующей системой"""
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or AnalyzerConfig()
        self.logger = logging.getLogger("analyzer.integration")
        
        # Основной движок анализатора
        self.analyzer_core = AnalyzerCore(config)
        
        # Сервисы существующей системы
        self.event_service = EventService()
        self.alert_service = AlertService()
        
        # Состояние интеграции
        self.is_integrated = False
        self.integration_start_time = None
        
        self.logger.info("AnalyzerIntegration initialized")
    
    async def integrate(self):
        """Интегрировать анализатор с существующей системой"""
        if self.is_integrated:
            self.logger.warning("Analyzer is already integrated")
            return
        
        try:
            self.logger.info("Starting analyzer integration...")
            
            # Запустить основной движок
            await self.analyzer_core.start()
            
            # Запустить фоновые задачи интеграции
            asyncio.create_task(self._event_ingestion_loop())
            asyncio.create_task(self._database_sync_loop())
            
            self.is_integrated = True
            self.integration_start_time = datetime.utcnow()
            
            self.logger.info("Analyzer integration completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to integrate analyzer: {e}")
            raise
    
    async def disintegrate(self):
        """Отключить интеграцию анализатора"""
        if not self.is_integrated:
            return
        
        try:
            self.logger.info("Disintegrating analyzer...")
            
            # Остановить основной движок
            await self.analyzer_core.stop()
            
            self.is_integrated = False
            self.integration_start_time = None
            
            self.logger.info("Analyzer disintegrated successfully")
            
        except Exception as e:
            self.logger.error(f"Error during disintegration: {e}")
            raise
    
    async def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обработать событие через интегрированный анализатор"""
        if not self.is_integrated:
            self.logger.warning("Analyzer is not integrated, cannot process event")
            return []
        
        try:
            # Обработать событие через основной движок
            results = await self.analyzer_core.process_event(event)
            
            if results:
                self.logger.info(f"Event processed, {len(results)} results generated")
                
                # Сохранить результаты в базу данных
                await self._save_analysis_results(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            return []
    
    async def process_events_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработать пакет событий"""
        if not self.is_integrated:
            self.logger.warning("Analyzer is not integrated, cannot process events")
            return []
        
        try:
            # Обработать события через основной движок
            results = await self.analyzer_core.process_events_batch(events)
            
            if results:
                self.logger.info(f"Batch processed, {len(results)} results generated")
                
                # Сохранить результаты в базу данных
                await self._save_analysis_results(results)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error processing events batch: {e}")
            return []
    
    async def _event_ingestion_loop(self):
        """Цикл приема событий из базы данных"""
        while self.is_integrated:
            try:
                await asyncio.sleep(self.config.processing_interval)
                
                if self.is_integrated:
                    await self._process_pending_events()
                    
            except Exception as e:
                self.logger.error(f"Error in event ingestion loop: {e}")
    
    async def _process_pending_events(self):
        """Обработать ожидающие события из базы данных"""
        try:
            # Получить новые события из базы данных
            with get_session() as session:
                # Здесь должна быть логика получения новых событий
                # Пока используем заглушку
                pending_events = await self._get_pending_events(session)
                
                if pending_events:
                    self.logger.info(f"Processing {len(pending_events)} pending events")
                    
                    # Обработать события через анализатор
                    results = await self.analyzer_core.process_events_batch(pending_events)
                    
                    if results:
                        self.logger.info(f"Generated {len(results)} analysis results")
                        
                        # Пометить события как обработанные
                        await self._mark_events_processed(session, [e.get("id") for e in pending_events])
        
        except Exception as e:
            self.logger.error(f"Error processing pending events: {e}")
    
    async def _get_pending_events(self, session) -> List[Dict[str, Any]]:
        """Получить ожидающие события из базы данных"""
        try:
            # Здесь должна быть реальная логика запроса к базе данных
            # Пока возвращаем пустой список
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting pending events: {e}")
            return []
    
    async def _mark_events_processed(self, session, event_ids: List[str]):
        """Пометить события как обработанные"""
        try:
            # Здесь должна быть логика обновления статуса событий
            # Пока просто логируем
            self.logger.debug(f"Marking {len(event_ids)} events as processed")
            
        except Exception as e:
            self.logger.error(f"Error marking events as processed: {e}")
    
    async def _database_sync_loop(self):
        """Цикл синхронизации с базой данных"""
        while self.is_integrated:
            try:
                await asyncio.sleep(60)  # Синхронизировать каждую минуту
                
                if self.is_integrated:
                    await self._sync_with_database()
                    
            except Exception as e:
                self.logger.error(f"Error in database sync loop: {e}")
    
    async def _sync_with_database(self):
        """Синхронизировать состояние с базой данных"""
        try:
            # Здесь может быть логика синхронизации конфигурации,
            # правил, статусов и т.д.
            self.logger.debug("Database sync completed")
            
        except Exception as e:
            self.logger.error(f"Error during database sync: {e}")
    
    async def _save_analysis_results(self, results: List[Dict[str, Any]]):
        """Сохранить результаты анализа в базу данных"""
        try:
            for result in results:
                # Сохранить алерт, если он был создан
                if "alert_id" in result:
                    # Алерт уже сохранен через AlertManager
                    continue
                
                # Сохранить другие результаты анализа
                await self._save_analysis_result(result)
        
        except Exception as e:
            self.logger.error(f"Error saving analysis results: {e}")
    
    async def _save_analysis_result(self, result: Dict[str, Any]):
        """Сохранить один результат анализа"""
        try:
            # Здесь может быть логика сохранения результатов анализа
            # в специальную таблицу или в метаданные событий
            self.logger.debug(f"Saving analysis result for rule: {result.get('rule_name')}")
            
        except Exception as e:
            self.logger.error(f"Error saving analysis result: {e}")
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Получить статус интеграции"""
        return {
            "is_integrated": self.is_integrated,
            "integration_start_time": self.integration_start_time.isoformat() if self.integration_start_time else None,
            "analyzer_status": self.analyzer_core.get_status(),
            "config": self.config.to_dict()
        }
    
    async def reload_config(self, new_config: AnalyzerConfig):
        """Перезагрузить конфигурацию интеграции"""
        try:
            self.logger.info("Reloading integration configuration...")
            
            # Перезагрузить конфигурацию основного движка
            await self.analyzer_core.reload_config(new_config)
            
            # Обновить локальную конфигурацию
            self.config = new_config
            
            self.logger.info("Integration configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload integration configuration: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверить состояние интеграции"""
        try:
            analyzer_health = self.analyzer_core.get_status()
            
            # Проверить подключение к базе данных
            db_healthy = await self._check_database_health()
            
            # Проверить состояние сервисов
            services_healthy = await self._check_services_health()
            
            return {
                "status": "healthy" if all([analyzer_health["is_running"], db_healthy, services_healthy]) else "unhealthy",
                "analyzer": analyzer_health,
                "database": {"healthy": db_healthy},
                "services": {"healthy": services_healthy},
                "integration": {
                    "is_integrated": self.is_integrated,
                    "uptime": (datetime.utcnow() - self.integration_start_time).total_seconds() if self.integration_start_time else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _check_database_health(self) -> bool:
        """Проверить состояние базы данных"""
        try:
            with get_session() as session:
                # Простой запрос для проверки подключения
                from sqlalchemy import text
                session.execute(text("SELECT 1"))
                return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return False
    
    async def _check_services_health(self) -> bool:
        """Проверить состояние сервисов"""
        try:
            # Проверить основные сервисы
            # Пока возвращаем True, так как сервисы могут быть не инициализированы
            return True
        except Exception as e:
            self.logger.error(f"Services health check failed: {e}")
            return False


# Глобальный экземпляр интеграции
_analyzer_integration: Optional[AnalyzerIntegration] = None


async def get_analyzer_integration(config: Optional[AnalyzerConfig] = None) -> AnalyzerIntegration:
    """Получить глобальный экземпляр интеграции анализатора"""
    global _analyzer_integration
    
    if _analyzer_integration is None:
        _analyzer_integration = AnalyzerIntegration(config)
    
    return _analyzer_integration


async def initialize_analyzer_integration(config: Optional[AnalyzerConfig] = None) -> AnalyzerIntegration:
    """Инициализировать и запустить интеграцию анализатора"""
    integration = await get_analyzer_integration(config)
    
    if not integration.is_integrated:
        await integration.integrate()
    
    return integration


async def shutdown_analyzer_integration():
    """Остановить интеграцию анализатора"""
    global _analyzer_integration
    
    if _analyzer_integration and _analyzer_integration.is_integrated:
        await _analyzer_integration.disintegrate()
        _analyzer_integration = None
