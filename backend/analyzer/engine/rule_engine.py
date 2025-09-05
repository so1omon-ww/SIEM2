"""
Rule Engine - Основной движок правил для SIEM системы

Функциональность:
- Загрузка правил из YAML файлов
- Применение правил к событиям
- Обработка immediate и threshold правил
- Интеграция с уведомлениями и алертами
- Корреляция событий
- Угрозы и разведка
"""

from __future__ import annotations
import asyncio
import json
import logging
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable
from collections import defaultdict, deque

try:
    import yaml
except ImportError:
    yaml = None

from .rule import Rule, RuleType, RuleSeverity, RuleSet
from .notification_service import NotificationService, NotificationType, NotificationPriority
from .alert_manager import AlertManager, AlertType, AlertSeverity, AlertContext
from .correlation_engine import CorrelationEngine
from .threat_intelligence import ThreatIntelligenceService


class RuleEngine:
    """Основной движок правил для анализа событий"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger("rule_engine")
        self.config = self._load_config(config_path)
        
        # Компоненты системы
        self.rule_set = RuleSet()
        self.notification_service = NotificationService()
        self.alert_manager = AlertManager()
        self.correlation_engine = CorrelationEngine()
        self.threat_intelligence = ThreatIntelligenceService()
        
        # Состояние движка
        self.is_running = False
        self.last_processed_id = 0
        self.event_counters = defaultdict(int)
        self.rule_counters = defaultdict(int)
        
        # Очереди и кэши
        self.event_queue = asyncio.Queue()
        self.threshold_cache = defaultdict(lambda: deque(maxlen=1000))
        self.correlation_cache = defaultdict(list)
        
        # Статистика
        self.stats = {
            'events_processed': 0,
            'rules_triggered': 0,
            'alerts_created': 0,
            'notifications_sent': 0,
            'correlations_found': 0,
            'threats_detected': 0
        }
        
        # Загружаем правила
        self._load_rules()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Загружает конфигурацию движка правил"""
        default_config = {
            'rules_directory': 'rules',
            'auto_reload_rules': True,
            'reload_interval': 300,  # 5 минут
            'max_events_per_batch': 100,
            'processing_timeout': 30,
            'enable_correlation': True,
            'enable_threat_intelligence': True,
            'enable_notifications': True,
            'enable_alerts': True,
            'threshold_check_interval': 60,  # 1 минута
            'correlation_window': 3600,  # 1 час
            'max_correlation_events': 1000
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    if yaml:
                        user_config = yaml.safe_load(f) or {}
                    else:
                        user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
        
        return default_config
    
    def _load_rules(self):
        """Загружает правила из файлов"""
        rules_dir = Path(__file__).parent.parent / self.config['rules_directory']
        
        if not rules_dir.exists():
            self.logger.warning(f"Rules directory not found: {rules_dir}")
            return
        
        loaded_rules = []
        
        # Загружаем встроенные правила
        builtin_dir = rules_dir / "builtin"
        if builtin_dir.exists():
            loaded_rules.extend(self._load_rules_from_directory(builtin_dir))
        
        # Загружаем пользовательские правила
        custom_dir = rules_dir / "custom"
        if custom_dir.exists():
            loaded_rules.extend(self._load_rules_from_directory(custom_dir))
        
        # Загружаем правила из корневой директории
        loaded_rules.extend(self._load_rules_from_directory(rules_dir))
        
        # Создаем набор правил
        self.rule_set = RuleSet(loaded_rules)
        
        self.logger.info(f"Loaded {len(loaded_rules)} rules")
        
        # Логируем статистику по типам правил
        for rule_type in RuleType:
            count = len(self.rule_set.get_rules_by_type(rule_type))
            if count > 0:
                self.logger.info(f"  {rule_type.value}: {count}")
    
    def _load_rules_from_directory(self, directory: Path) -> List[Rule]:
        """Загружает правила из указанной директории"""
        rules = []
        
        for rule_file in directory.glob("*.yaml"):
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    if yaml:
                        data = yaml.safe_load(f) or {}
                    else:
                        data = json.load(f)
                    
                    # Поддержка как одиночных правил, так и наборов
                    if isinstance(data, dict):
                        if 'rules' in data:
                            # Набор правил
                            for rule_data in data['rules']:
                                try:
                                    rule = Rule.from_dict(rule_data)
                                    rules.append(rule)
                                except Exception as e:
                                    self.logger.error(f"Failed to load rule from {rule_file}: {e}")
                        else:
                            # Одиночное правило
                            try:
                                rule = Rule.from_dict(data)
                                rules.append(rule)
                            except Exception as e:
                                self.logger.error(f"Failed to load rule from {rule_file}: {e}")
                    elif isinstance(data, list):
                        # Список правил
                        for rule_data in data:
                            try:
                                rule = Rule.from_dict(rule_data)
                                rules.append(rule)
                            except Exception as e:
                                self.logger.error(f"Failed to load rule from {rule_file}: {e}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load rule file {rule_file}: {e}")
        
        return rules
    
    async def start(self):
        """Запускает движок правил"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Rule engine started")
        
        # Запускаем компоненты
        await self.notification_service.start()
        
        # Запускаем обработчики
        asyncio.create_task(self._event_processor())
        asyncio.create_task(self._threshold_processor())
        asyncio.create_task(self._correlation_processor())
        
        if self.config['auto_reload_rules']:
            asyncio.create_task(self._rule_reloader())
    
    async def stop(self):
        """Останавливает движок правил"""
        self.is_running = False
        self.logger.info("Rule engine stopped")
        
        # Останавливаем компоненты
        await self.notification_service.stop()
    
    async def process_event(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обрабатывает одно событие через движок правил"""
        results = []
        
        try:
            # Обрабатываем immediate правила
            immediate_results = await self._process_immediate_rules(event)
            results.extend(immediate_results)
            
            # Добавляем в кэш для threshold правил
            await self._add_to_threshold_cache(event)
            
            # Добавляем в кэш для корреляции
            await self._add_to_correlation_cache(event)
            
            # Обновляем статистику
            self.stats['events_processed'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to process event: {e}")
        
        return results
    
    async def process_events_batch(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обрабатывает пакет событий"""
        all_results = []
        
        for event in events:
            results = await self.process_event(event)
            all_results.extend(results)
        
        return all_results
    
    async def _process_immediate_rules(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Обрабатывает immediate правила для события"""
        results = []
        
        # Получаем все активные immediate правила
        immediate_rules = self.rule_set.get_rules_by_type(RuleType.IMMEDIATE)
        
        for rule in immediate_rules:
            try:
                if rule.matches_event(event):
                    # Правило сработало
                    result = await self._execute_rule(rule, event)
                    results.append(result)
                    
                    # Обновляем статистику
                    self.rule_counters[rule.name] += 1
                    self.stats['rules_triggered'] += 1
                    
            except Exception as e:
                self.logger.error(f"Failed to process rule {rule.name}: {e}")
        
        return results
    
    async def _execute_rule(self, rule: Rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет правило и возвращает результат"""
        result = {
            'rule_name': rule.name,
            'rule_type': rule.type.value,
            'event_id': event.get('id'),
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'actions_executed': []
        }
        
        # Выполняем действия правила
        for action in rule.actions:
            try:
                action_result = await self._execute_action(action, rule, event)
                result['actions_executed'].append(action_result)
            except Exception as e:
                self.logger.error(f"Failed to execute action {action.type}: {e}")
                result['actions_executed'].append({
                    'type': action.type,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return result
    
    async def _execute_action(self, action: Any, rule: Rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет действие правила"""
        if action.type == 'alert':
            return await self._execute_alert_action(action, rule, event)
        elif action.type == 'notification':
            return await self._execute_notification_action(action, rule, event)
        elif action.type == 'log':
            return await self._execute_log_action(action, rule, event)
        elif action.type == 'script':
            return await self._execute_script_action(action, rule, event)
        else:
            self.logger.warning(f"Unknown action type: {action.type}")
            return {'type': action.type, 'status': 'unknown'}
    
    async def _execute_alert_action(self, action: Any, rule: Rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет действие создания алерта"""
        if not self.config['enable_alerts']:
            return {'type': 'alert', 'status': 'disabled'}
        
        try:
            # Создаем контекст алерта
            context = AlertContext(
                source_ip=event.get('src_ip'),
                destination_ip=event.get('dst_ip'),
                source_port=event.get('src_port'),
                destination_port=event.get('dst_port'),
                protocol=event.get('protocol'),
                user=event.get('user'),
                timestamp=event.get('ts'),
                additional_data=event.get('details', {})
            )
            
            # Определяем важность алерта
            severity_mapping = {
                RuleSeverity.INFO: AlertSeverity.INFO,
                RuleSeverity.LOW: AlertSeverity.LOW,
                RuleSeverity.MEDIUM: AlertSeverity.MEDIUM,
                RuleSeverity.HIGH: AlertSeverity.HIGH,
                RuleSeverity.CRITICAL: AlertSeverity.CRITICAL
            }
            
            alert_severity = severity_mapping.get(rule.severity, AlertSeverity.MEDIUM)
            
            # Создаем алерт
            alert = self.alert_manager.create_alert(
                title=action.parameters.get('title', rule.title or f"Rule {rule.name} triggered"),
                description=action.parameters.get('description', rule.description or f"Event matched rule {rule.name}"),
                alert_type=AlertType.SECURITY,
                severity=alert_severity,
                source=rule.source,
                rule_name=rule.name,
                event_id=event.get('id'),
                agent_id=event.get('agent_id'),
                context=context,
                tags=rule.tags,
                category=rule.category
            )
            
            self.stats['alerts_created'] += 1
            
            return {
                'type': 'alert',
                'status': 'created',
                'alert_id': alert.id,
                'alert_title': alert.title
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create alert: {e}")
            return {'type': 'alert', 'status': 'failed', 'error': str(e)}
    
    async def _execute_notification_action(self, action: Any, rule: Rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет действие отправки уведомления"""
        if not self.config['enable_notifications']:
            return {'type': 'notification', 'status': 'disabled'}
        
        try:
            # Определяем приоритет уведомления
            priority_mapping = {
                RuleSeverity.INFO: NotificationPriority.LOW,
                RuleSeverity.LOW: NotificationPriority.LOW,
                RuleSeverity.MEDIUM: NotificationPriority.NORMAL,
                RuleSeverity.HIGH: NotificationPriority.HIGH,
                RuleSeverity.CRITICAL: NotificationPriority.CRITICAL
            }
            
            notification_priority = priority_mapping.get(rule.severity, NotificationPriority.NORMAL)
            
            # Отправляем уведомление
            notification_id = await self.notification_service.send_notification(
                notification_type=NotificationType.ALERT,
                priority=notification_priority,
                title=action.parameters.get('title', rule.title or f"Rule {rule.name} triggered"),
                message=action.parameters.get('message', rule.description or f"Event matched rule {rule.name}"),
                template=action.parameters.get('template'),
                rule_name=rule.name,
                event_id=event.get('id'),
                severity=rule.severity.value,
                **action.parameters
            )
            
            self.stats['notifications_sent'] += 1
            
            return {
                'type': 'notification',
                'status': 'sent',
                'notification_id': notification_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            return {'type': 'notification', 'status': 'failed', 'error': str(e)}
    
    async def _execute_log_action(self, action: Any, rule: Rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет действие логирования"""
        try:
            log_message = action.parameters.get('message', f"Rule {rule.name} triggered")
            log_level = action.parameters.get('level', 'info')
            
            # Логируем событие
            log_method = getattr(self.logger, log_level.lower(), self.logger.info)
            log_method(f"{log_message} - Event: {event.get('id')}, Rule: {rule.name}")
            
            return {
                'type': 'log',
                'status': 'logged',
                'level': log_level,
                'message': log_message
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute log action: {e}")
            return {'type': 'log', 'status': 'failed', 'error': str(e)}
    
    async def _execute_script_action(self, action: Any, rule: Rule, event: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет действие скрипта"""
        try:
            script_path = action.parameters.get('script')
            if not script_path:
                return {'type': 'script', 'status': 'no_script_path'}
            
            # TODO: Реализовать выполнение скриптов
            self.logger.info(f"Script action would execute: {script_path}")
            
            return {
                'type': 'script',
                'status': 'not_implemented',
                'script_path': script_path
            }
            
        except Exception as e:
            self.logger.error(f"Failed to execute script action: {e}")
            return {'type': 'script', 'status': 'failed', 'error': str(e)}
    
    async def _add_to_threshold_cache(self, event: Dict[str, Any]):
        """Добавляет событие в кэш для threshold правил"""
        threshold_rules = self.rule_set.get_rules_by_type(RuleType.THRESHOLD)
        
        for rule in threshold_rules:
            if rule.matches_event(event):
                # Создаем ключ для группировки
                group_key = self._create_threshold_group_key(rule, event)
                self.threshold_cache[group_key].append({
                    'event': event,
                    'timestamp': datetime.now(timezone.utc),
                    'rule': rule
                })
    
    def _create_threshold_group_key(self, rule: Rule, event: Dict[str, Any]) -> str:
        """Создает ключ группировки для threshold правила"""
        if rule.group_by:
            key_parts = []
            for field in rule.group_by:
                value = self._get_field_value(event, field)
                key_parts.append(f"{field}={value}")
            return f"{rule.name}:{':'.join(key_parts)}"
        else:
            return rule.name
    
    async def _add_to_correlation_cache(self, event: Dict[str, Any]):
        """Добавляет событие в кэш для корреляции"""
        if not self.config['enable_correlation']:
            return
        
        correlation_rules = self.rule_set.get_rules_by_type(RuleType.CORRELATION)
        
        for rule in correlation_rules:
            if rule.matches_event(event):
                correlation_key = f"{rule.name}:{event.get('src_ip', 'unknown')}"
                self.correlation_cache[correlation_key].append({
                    'event': event,
                    'timestamp': datetime.now(timezone.utc),
                    'rule': rule
                })
                
                # Ограничиваем размер кэша
                if len(self.correlation_cache[correlation_key]) > self.config['max_correlation_events']:
                    self.correlation_cache[correlation_key] = self.correlation_cache[correlation_key][-self.config['max_correlation_events']:]
    
    async def _event_processor(self):
        """Основной обработчик событий"""
        while self.is_running:
            try:
                # Получаем событие из очереди
                event = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # Обрабатываем событие
                await self.process_event(event)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Event processor error: {e}")
    
    async def _threshold_processor(self):
        """Обработчик threshold правил"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['threshold_check_interval'])
                
                # Проверяем все threshold правила
                threshold_rules = self.rule_set.get_rules_by_type(RuleType.THRESHOLD)
                
                for rule in threshold_rules:
                    await self._check_threshold_rule(rule)
                    
            except Exception as e:
                self.logger.error(f"Threshold processor error: {e}")
    
    async def _check_threshold_rule(self, rule: Rule):
        """Проверяет threshold правило"""
        try:
            # Получаем окно времени
            window = rule.window_timedelta
            if not window:
                return
            
            cutoff_time = datetime.now(timezone.utc) - window
            
            # Проверяем все группы для этого правила
            for group_key, events in self.threshold_cache.items():
                if not group_key.startswith(rule.name):
                    continue
                
                # Фильтруем события по времени
                recent_events = [
                    e for e in events
                    if e['timestamp'] >= cutoff_time
                ]
                
                # Проверяем порог
                if len(recent_events) >= rule.threshold:
                    # Правило сработало
                    await self._execute_threshold_rule(rule, recent_events, group_key)
                    
        except Exception as e:
            self.logger.error(f"Failed to check threshold rule {rule.name}: {e}")
    
    async def _execute_threshold_rule(self, rule: Rule, events: List[Dict], group_key: str):
        """Выполняет threshold правило"""
        try:
            # Создаем агрегированное событие
            aggregated_event = {
                'id': f"threshold_{rule.name}_{hash(group_key)}",
                'event_type': f"threshold.{rule.name}",
                'ts': datetime.now(timezone.utc),
                'severity': rule.severity.value,
                'source': 'threshold_engine',
                'details': {
                    'rule_name': rule.name,
                    'threshold': rule.threshold,
                    'actual_count': len(events),
                    'group_key': group_key,
                    'events': [e['event']['id'] for e in events if e['event'].get('id')]
                }
            }
            
            # Выполняем правило
            result = await self._execute_rule(rule, aggregated_event)
            
            # Логируем результат
            self.logger.info(f"Threshold rule {rule.name} triggered: {len(events)} events in {group_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute threshold rule {rule.name}: {e}")
    
    async def _correlation_processor(self):
        """Обработчик корреляции событий"""
        while self.is_running:
            try:
                await asyncio.sleep(10)  # Проверяем каждые 10 секунд
                
                if not self.config['enable_correlation']:
                    continue
                
                # Проверяем корреляционные правила
                await self._check_correlation_rules()
                
            except Exception as e:
                self.logger.error(f"Correlation processor error: {e}")
    
    async def _check_correlation_rules(self):
        """Проверяет корреляционные правила"""
        try:
            correlation_rules = self.rule_set.get_rules_by_type(RuleType.CORRELATION)
            
            for rule in correlation_rules:
                await self._check_correlation_rule(rule)
                
        except Exception as e:
            self.logger.error(f"Failed to check correlation rules: {e}")
    
    async def _check_correlation_rule(self, rule: Rule):
        """Проверяет корреляционное правило"""
        try:
            # Получаем окно корреляции
            correlation_window = self.config['correlation_window']
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=correlation_window)
            
            # Проверяем все группы событий
            for correlation_key, events in self.correlation_cache.items():
                if not correlation_key.startswith(rule.name):
                    continue
                
                # Фильтруем события по времени
                recent_events = [
                    e for e in events
                    if e['timestamp'] >= cutoff_time
                ]
                
                # Проверяем условия корреляции
                if self._check_correlation_conditions(rule, recent_events):
                    await self._execute_correlation_rule(rule, recent_events, correlation_key)
                    
        except Exception as e:
            self.logger.error(f"Failed to check correlation rule {rule.name}: {e}")
    
    def _check_correlation_conditions(self, rule: Rule, events: List[Dict]) -> bool:
        """Проверяет условия корреляции"""
        # Простая реализация - можно расширить
        if not rule.conditions:
            return len(events) >= 2  # Минимум 2 события для корреляции
        
        # Проверяем специфические условия
        for condition, value in rule.conditions.items():
            if condition == 'min_events':
                if len(events) < value:
                    return False
            elif condition == 'max_events':
                if len(events) > value:
                    return False
            elif condition == 'time_window':
                if events:
                    first_time = events[0]['timestamp']
                    last_time = events[-1]['timestamp']
                    if (last_time - first_time).total_seconds() > value:
                        return False
        
        return True
    
    async def _execute_correlation_rule(self, rule: Rule, events: List[Dict], correlation_key: str):
        """Выполняет корреляционное правило"""
        try:
            # Создаем коррелированное событие
            correlated_event = {
                'id': f"correlation_{rule.name}_{hash(correlation_key)}",
                'event_type': f"correlation.{rule.name}",
                'ts': datetime.now(timezone.utc),
                'severity': rule.severity.value,
                'source': 'correlation_engine',
                'details': {
                    'rule_name': rule.name,
                    'correlation_key': correlation_key,
                    'events_count': len(events),
                    'events': [e['event']['id'] for e in events if e['event'].get('id')],
                    'time_span': (events[-1]['timestamp'] - events[0]['timestamp']).total_seconds() if len(events) > 1 else 0
                }
            }
            
            # Выполняем правило
            result = await self._execute_rule(rule, correlated_event)
            
            # Обновляем статистику
            self.stats['correlations_found'] += 1
            
            # Логируем результат
            self.logger.info(f"Correlation rule {rule.name} triggered: {len(events)} events in {correlation_key}")
            
        except Exception as e:
            self.logger.error(f"Failed to execute correlation rule {rule.name}: {e}")
    
    async def _rule_reloader(self):
        """Автоматическая перезагрузка правил"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['reload_interval'])
                
                if self.config['auto_reload_rules']:
                    self.logger.info("Reloading rules...")
                    self._load_rules()
                    
            except Exception as e:
                self.logger.error(f"Rule reloader error: {e}")
    
    def _get_field_value(self, event: Dict[str, Any], field_path: str) -> Any:
        """Получает значение поля из события по пути"""
        if "." not in field_path:
            return event.get(field_path)
        
        parts = field_path.split(".")
        current = event
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
            
            if current is None:
                break
        
        return current
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику движка правил"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'rules_loaded': len(self.rule_set.rules),
            'active_rules': len(self.rule_set.get_active_rules()),
            'event_queue_size': self.event_queue.qsize(),
            'threshold_cache_size': len(self.threshold_cache),
            'correlation_cache_size': len(self.correlation_cache),
            'rule_counters': dict(self.rule_counters),
            'event_counters': dict(self.event_counters)
        }
    
    def reload_rules(self):
        """Принудительно перезагружает правила"""
        self.logger.info("Manual rule reload requested")
        self._load_rules()
    
    def get_rule(self, rule_name: str) -> Optional[Rule]:
        """Получает правило по имени"""
        return self.rule_set.get_rule(rule_name)
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Получает правила по типу"""
        return self.rule_set.get_rules_by_type(rule_type)
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Получает правила по категории"""
        return self.rule_set.get_rules_by_category(category)
    
    def add_rule(self, rule: Rule):
        """Добавляет новое правило"""
        self.rule_set.add_rule(rule)
        self.logger.info(f"Added rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Удаляет правило"""
        self.rule_set.remove_rule(rule_name)
        self.logger.info(f"Removed rule: {rule_name}")


# Глобальный экземпляр движка правил
rule_engine = RuleEngine()


async def process_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Удобная функция для обработки события"""
    return await rule_engine.process_event(event)


async def process_events_batch(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Удобная функция для обработки пакета событий"""
    return await rule_engine.process_events_batch(events)


def get_rule_engine() -> RuleEngine:
    """Возвращает глобальный экземпляр движка правил"""
    return rule_engine
