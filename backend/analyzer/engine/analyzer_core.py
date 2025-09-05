"""
Основной движок анализатора SIEM
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path

from .rule_engine import RuleEngine
from .correlation_engine import CorrelationEngine
from .threat_intelligence import ThreatIntelligenceService
from .notification_service import NotificationService
from .alert_manager import AlertManager
from .rule import RuleSet
from ..config import AnalyzerConfig
from ..utils import EventMatcher, TimeWindow, EventAggregator, DeduplicationManager
from .rule import RuleType


class AnalyzerCore:
    """Основной движок анализатора"""
    
    def __init__(self, config: Optional[AnalyzerConfig] = None):
        self.config = config or AnalyzerConfig()
        self.logger = logging.getLogger("analyzer.core")
        
        # Инициализация компонентов
        self.rule_engine = RuleEngine(config)
        self.correlation_engine = CorrelationEngine(config)
        self.threat_intelligence = ThreatIntelligenceService(config)
        self.notification_service = NotificationService(config)
        self.alert_manager = AlertManager(config)
        
        # Утилиты
        self.dedup_manager = DeduplicationManager()
        
        # Состояние
        self.is_running = False
        self.last_rule_reload = datetime.utcnow()
        self.processed_events_count = 0
        self.triggered_rules_count = 0
        self.generated_alerts_count = 0
        
        # Кеш событий для корреляции
        self.event_cache: List[Dict[str, Any]] = []
        self.cache_lock = asyncio.Lock()
        
        self.logger.info("AnalyzerCore initialized")
    
    async def start(self):
        """Запустить движок анализатора"""
        if self.is_running:
            self.logger.warning("Analyzer is already running")
            return
        
        self.logger.info("Starting analyzer core...")
        self.is_running = True
        
        try:
            # Загрузить правила
            await self._load_rules()
            
            # Запустить фоновые задачи
            asyncio.create_task(self._rule_reload_loop())
            asyncio.create_task(self._correlation_loop())
            asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Analyzer core started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start analyzer core: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Остановить движок анализатора"""
        if not self.is_running:
            return
        
        self.logger.info("Stopping analyzer core...")
        self.is_running = False
        
        # Остановить фоновые задачи
        await asyncio.sleep(1)  # Дать время на завершение
        
        self.logger.info("Analyzer core stopped")
    
    async def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обработать одно событие"""
        if not self.is_running:
            self.logger.warning("Analyzer is not running, skipping event")
            return []
        
        try:
            self.processed_events_count += 1
            
            # Добавить событие в кеш для корреляции
            async with self.cache_lock:
                self.event_cache.append(event)
                
                # Ограничить размер кеша
                if len(self.event_cache) > self.config.max_correlation_events:
                    self.event_cache = self.event_cache[-self.config.max_correlation_events:]
            
            # Обработать немедленные правила
            immediate_results = await self._process_immediate_rules(event)
            
            # Обработать правила порога
            threshold_results = await self._process_threshold_rules(event)
            
            # Объединить результаты
            all_results = immediate_results + threshold_results
            
            if all_results:
                self.triggered_rules_count += len(all_results)
                self.logger.info(f"Event triggered {len(all_results)} rules")
            
            return all_results
            
        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            return []
    
    async def process_events_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработать пакет событий"""
        if not events:
            return []
        
        self.logger.info(f"Processing batch of {len(events)} events")
        
        all_results = []
        
        # Обработать события параллельно
        tasks = [self.process_event(event) for event in events]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"Error in batch processing: {result}")
            elif isinstance(result, list):
                all_results.extend(result)
        
        self.logger.info(f"Batch processing completed, {len(all_results)} results generated")
        return all_results
    
    async def _load_rules(self):
        """Загрузить правила"""
        try:
            self.rule_engine._load_rules()
            self.last_rule_reload = datetime.utcnow()
            self.logger.info("Rules loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load rules: {e}")
            raise
    
    async def _process_immediate_rules(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обработать немедленные правила"""
        results = []
        
        try:
            immediate_rules = self.rule_engine.get_rules_by_type(RuleType.IMMEDIATE)
            
            for rule in immediate_rules:
                if EventMatcher.match_event(event, rule.matches):
                    result = await self._execute_rule(rule, event)
                    if result:
                        results.append(result)
                        
                        # Проверить дедупликацию
                        if rule.dedup_key:
                            dedup_key = self._build_dedup_key(rule.dedup_key, event)
                            if self.dedup_manager.is_duplicate(dedup_key):
                                continue
        
        except Exception as e:
            self.logger.error(f"Error processing immediate rules: {e}")
        
        return results
    
    async def _process_threshold_rules(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обработать правила порога"""
        results = []
        
        try:
            threshold_rules = self.rule_engine.get_rules_by_type(RuleType.THRESHOLD)
            
            for rule in threshold_rules:
                if EventMatcher.match_event(event, rule.matches):
                    # Проверить, достигнут ли порог
                    if await self._check_threshold(rule, event):
                        result = await self._execute_rule(rule, event)
                        if result:
                            results.append(result)
        
        except Exception as e:
            self.logger.error(f"Error processing threshold rules: {e}")
        
        return results
    
    async def _check_threshold(self, rule, event: Dict[str, Any]) -> bool:
        """Проверить, достигнут ли порог для правила"""
        try:
            window_start = TimeWindow.get_window_start(rule.window)
            
            # Получить события в окне
            async with self.cache_lock:
                window_events = [
                    e for e in self.event_cache
                    if e.get("event_type") == event.get("event_type") and
                    TimeWindow.is_in_window(
                        datetime.fromisoformat(e.get("timestamp", "").replace('Z', '+00:00')),
                        rule.window
                    )
                ]
            
            # Группировать события
            if rule.group_by:
                grouped_events = EventAggregator.group_events(window_events, rule.group_by)
                
                # Проверить каждую группу
                for group_key, group_events in grouped_events.items():
                    if len(group_events) >= rule.threshold:
                        return True
            else:
                # Простая проверка количества
                if len(window_events) >= rule.threshold:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking threshold: {e}")
            return False
    
    async def _execute_rule(self, rule, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Выполнить правило"""
        try:
            result = {
                "rule_name": rule.name,
                "rule_type": rule.type,
                "severity": rule.severity,
                "category": rule.category,
                "event": event,
                "timestamp": datetime.utcnow().isoformat(),
                "actions": []
            }
            
            # Выполнить действия
            for action in rule.actions:
                action_result = await self._execute_action(action, rule, event)
                if action_result:
                    result["actions"].append(action_result)
            
            # Создать уведомления
            if result["actions"]:
                await self._create_notifications(rule, event, result)
                
                # Создать алерт
                alert = await self.alert_manager.create_alert(
                    title=result.get("title", f"Rule triggered: {rule.name}"),
                    description=result.get("description", rule.description),
                    severity=rule.severity,
                    category=rule.category,
                    source_event=event,
                    rule_name=rule.name
                )
                
                if alert:
                    result["alert_id"] = alert.id
                    self.generated_alerts_count += 1
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing rule {rule.name}: {e}")
            return None
    
    async def _execute_action(self, action: Dict[str, Any], rule, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Выполнить действие правила"""
        try:
            action_type = action.get("type")
            
            if action_type == "alert":
                return await self._execute_alert_action(action, rule, event)
            
            elif action_type == "notification":
                return await self._execute_notification_action(action, rule, event)
            
            elif action_type == "log":
                return await self._execute_log_action(action, rule, event)
            
            else:
                self.logger.warning(f"Unknown action type: {action_type}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error executing action {action.get('type')}: {e}")
            return None
    
    async def _execute_alert_action(self, action: Dict[str, Any], rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить действие создания алерта"""
        title = action.get("parameters", {}).get("title", f"Alert: {rule.name}")
        description = action.get("parameters", {}).get("description", rule.description)
        
        alert = await self.alert_manager.create_alert(
            title=title,
            description=description,
            severity=rule.severity,
            category=rule.category,
            source_event=event,
            rule_name=rule.name
        )
        
        return {
            "type": "alert",
            "alert_id": alert.id if alert else None,
            "title": title,
            "description": description
        }
    
    async def _execute_notification_action(self, action: Dict[str, Any], rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить действие отправки уведомления"""
        template_name = action.get("parameters", {}).get("template", "general_alert")
        title = action.get("parameters", {}).get("title", f"Notification: {rule.name}")
        message = action.get("parameters", {}).get("message", rule.description)
        
        notification = await self.notification_service.send_notification(
            template_name=template_name,
            title=title,
            message=message,
            priority=action.get("priority", 3),
            channels=action.get("channels", ["agent", "log"]),
            context={"event": event, "rule": rule}
        )
        
        return {
            "type": "notification",
            "notification_id": notification.id if notification else None,
            "title": title,
            "message": message
        }
    
    async def _execute_log_action(self, action: Dict[str, Any], rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнить действие логирования"""
        message = action.get("parameters", {}).get("message", f"Rule {rule.name} triggered")
        level = action.get("parameters", {}).get("level", "info")
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message)
        
        return {
            "type": "log",
            "message": message,
            "level": level
        }
    
    async def _create_notifications(self, rule, event: Dict[str, Any], result: Dict[str, Any]):
        """Создать уведомления для правила"""
        try:
            # Определить каналы уведомлений
            channels = set()
            for action in result.get("actions", []):
                if action.get("type") == "notification":
                    channels.update(action.get("channels", ["agent", "log"]))
            
            if not channels:
                channels = {"agent", "log"}
            
            # Отправить уведомления
            for channel in channels:
                if self.config.is_channel_enabled(channel):
                    await self.notification_service.send_notification(
                        template_name="threat_detected",
                        title=f"Rule triggered: {rule.name}",
                        message=f"Rule {rule.name} triggered for event {event.get('event_type')}",
                        priority=1,
                        channels=[channel],
                        context={"event": event, "rule": rule, "result": result}
                    )
        
        except Exception as e:
            self.logger.error(f"Error creating notifications: {e}")
    
    def _build_dedup_key(self, dedup_template: str, event: Dict[str, Any]) -> str:
        """Построить ключ дедупликации"""
        try:
            # Заменить переменные в шаблоне
            key = dedup_template
            for field, value in event.items():
                key = key.replace(f"{{{field}}}", str(value))
            
            # Заменить вложенные поля
            if "details" in event and isinstance(event["details"], dict):
                for field, value in event["details"].items():
                    key = key.replace(f"{{details.{field}}}", str(value))
            
            return key
        except Exception as e:
            self.logger.error(f"Error building dedup key: {e}")
            return f"dedup_{event.get('id', 'unknown')}"
    
    async def _rule_reload_loop(self):
        """Цикл перезагрузки правил"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config.rule_reload_interval)
                
                if self.is_running:
                    await self._load_rules()
                    
            except Exception as e:
                self.logger.error(f"Error in rule reload loop: {e}")
    
    async def _correlation_loop(self):
        """Цикл корреляции событий"""
        while self.is_running:
            try:
                await asyncio.sleep(30)  # Проверять каждые 30 секунд
                
                if self.is_running and self.config.correlation_enabled:
                    await self._run_correlation()
                    
            except Exception as e:
                self.logger.error(f"Error in correlation loop: {e}")
    
    async def _cleanup_loop(self):
        """Цикл очистки"""
        while self.is_running:
            try:
                await asyncio.sleep(300)  # Очищать каждые 5 минут
                
                if self.is_running:
                    await self._cleanup_old_data()
                    
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
    
    async def _run_correlation(self):
        """Запустить корреляцию событий"""
        try:
            async with self.cache_lock:
                if len(self.event_cache) < 2:
                    return
                
                # Получить события для корреляции
                correlation_window = datetime.utcnow() - timedelta(seconds=self.config.correlation_window)
                recent_events = [
                    e for e in self.event_cache
                    if TimeWindow.is_in_window(
                        datetime.fromisoformat(e.get("timestamp", "").replace('Z', '+00:00')),
                        f"{self.config.correlation_window}s"
                    )
                ]
                
                if len(recent_events) < 2:
                    return
                
                # Запустить корреляцию
                correlation_results = await self.correlation_engine.correlate_events(recent_events)
                
                if correlation_results:
                    self.logger.info(f"Correlation found {len(correlation_results)} patterns")
                    
                    # Обработать результаты корреляции
                    for result in correlation_results:
                        await self._handle_correlation_result(result)
        
        except Exception as e:
            self.logger.error(f"Error running correlation: {e}")
    
    async def _handle_correlation_result(self, correlation_result: Dict[str, Any]):
        """Обработать результат корреляции"""
        try:
            # Создать алерт для корреляции
            alert = await self.alert_manager.create_alert(
                title=f"Correlation detected: {correlation_result.get('type', 'unknown')}",
                description=correlation_result.get("description", "Event correlation detected"),
                severity=correlation_result.get("severity", "medium"),
                category="correlation",
                source_event=correlation_result.get("events", [{}])[0],
                metadata={"correlation": correlation_result}
            )
            
            if alert:
                # Отправить уведомление
                await self.notification_service.send_notification(
                    template_name="threat_detected",
                    title="🔗 Корреляция событий",
                    message=f"Обнаружена корреляция: {correlation_result.get('description', '')}",
                    priority=2,
                    channels=["agent", "log"],
                    context={"correlation": correlation_result, "alert": alert}
                )
        
        except Exception as e:
            self.logger.error(f"Error handling correlation result: {e}")
    
    async def _cleanup_old_data(self):
        """Очистить старые данные"""
        try:
            # Очистить кеш событий
            cutoff_time = datetime.utcnow() - timedelta(seconds=self.config.correlation_window * 2)
            
            async with self.cache_lock:
                self.event_cache = [
                    e for e in self.event_cache
                    if TimeWindow.is_in_window(
                        datetime.fromisoformat(e.get("timestamp", "").replace('Z', '+00:00')),
                        f"{self.config.correlation_window * 2}s"
                    )
                ]
            
            # Очистить кеш дедупликации
            self.dedup_manager.clear_cache()
            
            self.logger.debug("Cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Получить статус анализатора"""
        return {
            "is_running": self.is_running,
            "processed_events_count": self.processed_events_count,
            "triggered_rules_count": self.triggered_rules_count,
            "generated_alerts_count": self.generated_alerts_count,
            "event_cache_size": len(self.event_cache),
            "last_rule_reload": self.last_rule_reload.isoformat(),
            "config": self.config.to_dict()
        }
    
    async def reload_config(self, new_config: AnalyzerConfig):
        """Перезагрузить конфигурацию"""
        try:
            self.logger.info("Reloading analyzer configuration...")
            
            # Остановить текущие процессы
            old_running = self.is_running
            if old_running:
                await self.stop()
            
            # Обновить конфигурацию
            self.config = new_config
            
            # Перезапустить, если был запущен
            if old_running:
                await self.start()
            
            self.logger.info("Configuration reloaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to reload configuration: {e}")
            raise
