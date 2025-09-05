"""
Alert Manager - Менеджер алертов для SIEM системы

Управляет:
- Созданием алертов
- Жизненным циклом алертов
- Статусами и переходами
- Дублированием и группировкой
- Эскалацией алертов
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import asyncio
import json
import logging
import hashlib
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


class AlertStatus(str, Enum):
    """Статусы алертов"""
    NEW = "new"                    # Новый алерт
    ACKNOWLEDGED = "acknowledged"  # Подтвержден
    IN_PROGRESS = "in_progress"    # В работе
    RESOLVED = "resolved"          # Решен
    CLOSED = "closed"              # Закрыт
    ESCALATED = "escalated"        # Эскалирован


class AlertSeverity(str, Enum):
    """Уровни важности алертов"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Типы алертов"""
    SECURITY = "security"          # Безопасность
    NETWORK = "network"            # Сеть
    SYSTEM = "system"              # Система
    APPLICATION = "application"     # Приложение
    USER = "user"                  # Пользователь
    COMPLIANCE = "compliance"      # Соответствие


@dataclass
class AlertContext:
    """Контекст алерта"""
    source_ip: Optional[str] = None
    destination_ip: Optional[str] = None
    source_port: Optional[int] = None
    destination_port: Optional[int] = None
    protocol: Optional[str] = None
    user: Optional[str] = None
    process: Optional[str] = None
    file: Optional[str] = None
    url: Optional[str] = None
    timestamp: Optional[datetime] = None
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Алерт безопасности"""
    # Основные параметры
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    alert_type: AlertType = AlertType.SECURITY
    severity: AlertSeverity = AlertSeverity.MEDIUM
    status: AlertStatus = AlertStatus.NEW
    
    # Источник и контекст
    source: str = "analyzer"
    rule_name: Optional[str] = None
    event_id: Optional[int] = None
    agent_id: Optional[int] = None
    
    # Контекст
    context: AlertContext = field(default_factory=AlertContext)
    
    # Метаданные
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    confidence: float = 0.8  # 0.0 - 1.0
    
    # Временные метки
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    
    # Жизненный цикл
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    closed_by: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    
    # Дублирование и группировка
    dedup_key: Optional[str] = None
    group_id: Optional[str] = None
    related_alerts: List[int] = field(default_factory=list)
    
    # Эскалация
    escalation_level: int = 0
    max_escalation_level: int = 3
    escalation_rules: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = self.created_at
        
        # Генерируем dedup_key если не задан
        if not self.dedup_key:
            self.dedup_key = self._generate_dedup_key()
    
    def _generate_dedup_key(self) -> str:
        """Генерирует ключ для дедупликации"""
        key_parts = [
            self.source,
            self.rule_name or "",
            str(self.context.source_ip or ""),
            str(self.context.destination_ip or ""),
            str(self.context.source_port or ""),
            str(self.context.destination_port or ""),
            str(self.context.protocol or ""),
            str(self.context.user or ""),
            str(self.alert_type.value),
            str(self.severity.value)
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует алерт в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'source': self.source,
            'rule_name': self.rule_name,
            'event_id': self.event_id,
            'agent_id': self.agent_id,
            'context': {
                'source_ip': self.context.source_ip,
                'destination_ip': self.context.destination_ip,
                'source_port': self.context.source_port,
                'destination_port': self.context.destination_port,
                'protocol': self.context.protocol,
                'user': self.context.user,
                'process': self.context.process,
                'file': self.context.file,
                'url': self.context.url,
                'timestamp': self.context.timestamp.isoformat() if self.context.timestamp else None,
                'additional_data': self.context.additional_data
            },
            'tags': self.tags,
            'category': self.category,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_by': self.resolved_by,
            'closed_by': self.closed_by,
            'notes': self.notes,
            'dedup_key': self.dedup_key,
            'group_id': self.group_id,
            'related_alerts': self.related_alerts,
            'escalation_level': self.escalation_level,
            'max_escalation_level': self.max_escalation_level,
            'escalation_rules': self.escalation_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Создает алерт из словаря"""
        # Преобразуем enum значения
        data['alert_type'] = AlertType(data['alert_type'])
        data['severity'] = AlertSeverity(data['severity'])
        data['status'] = AlertStatus(data['status'])
        
        # Преобразуем контекст
        if 'context' in data:
            context_data = data['context']
            if 'timestamp' in context_data and context_data['timestamp']:
                context_data['timestamp'] = datetime.fromisoformat(context_data['timestamp'])
            data['context'] = AlertContext(**context_data)
        
        # Преобразуем даты
        date_fields = ['created_at', 'updated_at', 'acknowledged_at', 'resolved_at', 'closed_at']
        for field_name in date_fields:
            if field_name in data and data[field_name]:
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)
    
    def acknowledge(self, user: str, note: str = None):
        """Подтверждает алерт"""
        if self.status != AlertStatus.NEW:
            raise ValueError(f"Cannot acknowledge alert in status {self.status}")
        
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = user
        self.updated_at = datetime.now(timezone.utc)
        
        if note:
            self.notes.append(f"[{datetime.now(timezone.utc).isoformat()}] {user}: {note}")
    
    def start_progress(self, user: str, note: str = None):
        """Начинает работу над алертом"""
        if self.status not in [AlertStatus.NEW, AlertStatus.ACKNOWLEDGED]:
            raise ValueError(f"Cannot start progress on alert in status {self.status}")
        
        self.status = AlertStatus.IN_PROGRESS
        self.updated_at = datetime.now(timezone.utc)
        
        if note:
            self.notes.append(f"[{datetime.now(timezone.utc).isoformat()}] {user}: {note}")
    
    def resolve(self, user: str, note: str = None):
        """Решает алерт"""
        if self.status not in [AlertStatus.IN_PROGRESS, AlertStatus.ACKNOWLEDGED]:
            raise ValueError(f"Cannot resolve alert in status {self.status}")
        
        self.status = AlertStatus.RESOLVED
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = user
        self.updated_at = datetime.now(timezone.utc)
        
        if note:
            self.notes.append(f"[{datetime.now(timezone.utc).isoformat()}] {user}: {note}")
    
    def close(self, user: str, note: str = None):
        """Закрывает алерт"""
        if self.status not in [AlertStatus.RESOLVED, AlertStatus.ACKNOWLEDGED]:
            raise ValueError(f"Cannot close alert in status {self.status}")
        
        self.status = AlertStatus.CLOSED
        self.closed_at = datetime.now(timezone.utc)
        self.closed_by = user
        self.updated_at = datetime.now(timezone.utc)
        
        if note:
            self.notes.append(f"[{datetime.now(timezone.utc).isoformat()}] {user}: {note}")
    
    def escalate(self, escalation_rule: str, note: str = None):
        """Эскалирует алерт"""
        if self.escalation_level >= self.max_escalation_level:
            raise ValueError(f"Alert already at maximum escalation level {self.max_escalation_level}")
        
        self.escalation_level += 1
        self.status = AlertStatus.ESCALATED
        self.updated_at = datetime.now(timezone.utc)
        self.escalation_rules.append(escalation_rule)
        
        if note:
            self.notes.append(f"[{datetime.now(timezone.utc).isoformat()}] ESCALATED: {note}")
    
    def add_note(self, user: str, note: str):
        """Добавляет заметку к алерту"""
        timestamp = datetime.now(timezone.utc).isoformat()
        self.notes.append(f"[{timestamp}] {user}: {note}")
        self.updated_at = datetime.now(timezone.utc)
    
    def is_duplicate_of(self, other: 'Alert') -> bool:
        """Проверяет, является ли алерт дубликатом другого"""
        return self.dedup_key == other.dedup_key
    
    def can_group_with(self, other: 'Alert') -> bool:
        """Проверяет, можно ли сгруппировать алерты"""
        # Простая логика группировки - можно расширить
        return (
            self.alert_type == other.alert_type and
            self.severity == other.severity and
            self.context.source_ip == other.context.source_ip and
            abs((self.created_at - other.created_at).total_seconds()) < 3600  # 1 час
        )
    
    def get_age(self) -> timedelta:
        """Возвращает возраст алерта"""
        return datetime.now(timezone.utc) - self.created_at
    
    def is_stale(self, max_age_hours: int = 24) -> bool:
        """Проверяет, устарел ли алерт"""
        return self.get_age().total_seconds() > max_age_hours * 3600
    
    def requires_escalation(self) -> bool:
        """Проверяет, требует ли алерт эскалации"""
        if self.status in [AlertStatus.RESOLVED, AlertStatus.CLOSED]:
            return False
        
        # Эскалация по времени
        if self.status == AlertStatus.NEW and self.get_age().total_seconds() > 3600:  # 1 час
            return True
        
        if self.status == AlertStatus.ACKNOWLEDGED and self.get_age().total_seconds() > 7200:  # 2 часа
            return True
        
        # Эскалация по важности
        if self.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            if self.status == AlertStatus.NEW and self.get_age().total_seconds() > 1800:  # 30 минут
                return True
        
        return False


class AlertLifecycle:
    """Управление жизненным циклом алертов"""
    
    def __init__(self):
        self.logger = logging.getLogger("alert_lifecycle")
        self.escalation_rules = self._load_escalation_rules()
    
    def _load_escalation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Загружает правила эскалации"""
        # Встроенные правила эскалации
        return {
            'time_based': {
                'new_alert': 3600,      # 1 час
                'acknowledged': 7200,    # 2 часа
                'in_progress': 14400     # 4 часа
            },
            'severity_based': {
                'critical': 900,         # 15 минут
                'high': 1800,            # 30 минут
                'medium': 3600,          # 1 час
                'low': 7200              # 2 часа
            }
        }
    
    def should_escalate(self, alert: Alert) -> bool:
        """Проверяет, должна ли произойти эскалация"""
        return alert.requires_escalation()
    
    def get_escalation_action(self, alert: Alert) -> Optional[str]:
        """Возвращает действие эскалации для алерта"""
        if not self.should_escalate(alert):
            return None
        
        # Определяем правило эскалации
        if alert.severity == AlertSeverity.CRITICAL:
            return "immediate_escalation"
        elif alert.severity == AlertSeverity.HIGH:
            return "high_priority_escalation"
        elif alert.status == AlertStatus.NEW and alert.get_age().total_seconds() > 3600:
            return "time_based_escalation"
        elif alert.status == AlertStatus.ACKNOWLEDGED and alert.get_age().total_seconds() > 7200:
            return "acknowledgment_timeout_escalation"
        
        return None
    
    def apply_escalation(self, alert: Alert, escalation_action: str):
        """Применяет эскалацию к алерту"""
        if escalation_action == "immediate_escalation":
            alert.escalate("immediate", "Critical alert requires immediate attention")
        elif escalation_action == "high_priority_escalation":
            alert.escalate("high_priority", "High priority alert escalated")
        elif escalation_action == "time_based_escalation":
            alert.escalate("time_based", "Alert escalated due to time threshold")
        elif escalation_action == "acknowledgment_timeout_escalation":
            alert.escalate("acknowledgment_timeout", "Alert escalated due to acknowledgment timeout")
        
        self.logger.info(f"Alert {alert.id} escalated with action: {escalation_action}")


class AlertManager:
    """Основной менеджер алертов"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger("alert_manager")
        self.config = config or {}
        self.alerts: Dict[int, Alert] = {}
        self.alerts_by_dedup: Dict[str, Alert] = {}
        self.alerts_by_group: Dict[str, List[Alert]] = {}
        self.lifecycle = AlertLifecycle()
        
        # Статистика
        self.stats = {
            'total_created': 0,
            'total_acknowledged': 0,
            'total_resolved': 0,
            'total_closed': 0,
            'total_escalated': 0,
            'duplicates_prevented': 0,
            'groups_created': 0
        }
        
        # Счетчик для генерации ID
        self._next_id = 1
    
    def create_alert(
        self,
        title: str,
        description: str,
        alert_type: AlertType = AlertType.SECURITY,
        severity: AlertSeverity = AlertSeverity.MEDIUM,
        source: str = "analyzer",
        rule_name: Optional[str] = None,
        event_id: Optional[int] = None,
        agent_id: Optional[int] = None,
        context: Optional[AlertContext] = None,
        **kwargs
    ) -> Alert:
        """Создает новый алерт"""
        # Проверяем на дубликаты
        if context and context.source_ip:
            dedup_key = self._generate_dedup_key(title, source, rule_name, context)
            if dedup_key in self.alerts_by_dedup:
                existing_alert = self.alerts_by_dedup[dedup_key]
                self.logger.info(f"Duplicate alert prevented: {existing_alert.id}")
                self.stats['duplicates_prevented'] += 1
                return existing_alert
        
        # Создаем алерт
        alert = Alert(
            id=self._next_id,
            title=title,
            description=description,
            alert_type=alert_type,
            severity=severity,
            source=source,
            rule_name=rule_name,
            event_id=event_id,
            agent_id=agent_id,
            context=context or AlertContext(),
            **kwargs
        )
        
        # Сохраняем алерт
        self.alerts[alert.id] = alert
        if alert.dedup_key:
            self.alerts_by_dedup[alert.dedup_key] = alert
        
        # Группируем алерты
        self._try_group_alert(alert)
        
        # Увеличиваем счетчик
        self._next_id += 1
        self.stats['total_created'] += 1
        
        self.logger.info(f"Created alert {alert.id}: {title}")
        return alert
    
    def _generate_dedup_key(self, title: str, source: str, rule_name: Optional[str], context: AlertContext) -> str:
        """Генерирует ключ дедупликации"""
        key_parts = [
            source,
            rule_name or "",
            str(context.source_ip or ""),
            str(context.destination_ip or ""),
            str(context.source_port or ""),
            str(context.destination_port or ""),
            str(context.protocol or ""),
            str(context.user or ""),
            title
        ]
        
        key_string = "|".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _try_group_alert(self, alert: Alert):
        """Пытается сгруппировать алерт с существующими"""
        for group_id, group_alerts in self.alerts_by_group.items():
            if group_alerts and alert.can_group_with(group_alerts[0]):
                group_alerts.append(alert)
                alert.group_id = group_id
                self.logger.info(f"Alert {alert.id} added to group {group_id}")
                return
        
        # Создаем новую группу
        group_id = f"group_{len(self.alerts_by_group) + 1}"
        self.alerts_by_group[group_id] = [alert]
        alert.group_id = group_id
        self.stats['groups_created'] += 1
        
        self.logger.info(f"Created new alert group {group_id} for alert {alert.id}")
    
    def get_alert(self, alert_id: int) -> Optional[Alert]:
        """Получает алерт по ID"""
        return self.alerts.get(alert_id)
    
    def get_alerts_by_status(self, status: AlertStatus) -> List[Alert]:
        """Получает алерты по статусу"""
        return [alert for alert in self.alerts.values() if alert.status == status]
    
    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Получает алерты по важности"""
        return [alert for alert in self.alerts.values() if alert.severity == severity]
    
    def get_alerts_by_type(self, alert_type: AlertType) -> List[Alert]:
        """Получает алерты по типу"""
        return [alert for alert in self.alerts.values() if alert.alert_type == alert_type]
    
    def get_alerts_by_source(self, source: str) -> List[Alert]:
        """Получает алерты по источнику"""
        return [alert for alert in self.alerts.values() if alert.source == source]
    
    def get_alerts_by_group(self, group_id: str) -> List[Alert]:
        """Получает алерты по группе"""
        return self.alerts_by_group.get(group_id, [])
    
    def get_alerts_by_time_range(self, start_time: datetime, end_time: datetime) -> List[Alert]:
        """Получает алерты в временном диапазоне"""
        return [
            alert for alert in self.alerts.values()
            if start_time <= alert.created_at <= end_time
        ]
    
    def get_recent_alerts(self, hours: int = 24) -> List[Alert]:
        """Получает недавние алерты"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        return self.get_alerts_by_time_range(cutoff_time, datetime.now(timezone.utc))
    
    def acknowledge_alert(self, alert_id: int, user: str, note: str = None) -> bool:
        """Подтверждает алерт"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        try:
            alert.acknowledge(user, note)
            self.stats['total_acknowledged'] += 1
            self.logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        except ValueError as e:
            self.logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    def resolve_alert(self, alert_id: int, user: str, note: str = None) -> bool:
        """Решает алерт"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        try:
            alert.resolve(user, note)
            self.stats['total_resolved'] += 1
            self.logger.info(f"Alert {alert_id} resolved by {user}")
            return True
        except ValueError as e:
            self.logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    def close_alert(self, alert_id: int, user: str, note: str = None) -> bool:
        """Закрывает алерт"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        try:
            alert.close(user, note)
            self.stats['total_closed'] += 1
            self.logger.info(f"Alert {alert_id} closed by {user}")
            return True
        except ValueError as e:
            self.logger.error(f"Failed to close alert {alert_id}: {e}")
            return False
    
    def escalate_alert(self, alert_id: int, escalation_rule: str, note: str = None) -> bool:
        """Эскалирует алерт"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        try:
            alert.escalate(escalation_rule, note)
            self.stats['total_escalated'] += 1
            self.logger.info(f"Alert {alert_id} escalated with rule {escalation_rule}")
            return True
        except ValueError as e:
            self.logger.error(f"Failed to escalate alert {alert_id}: {e}")
            return False
    
    def add_note_to_alert(self, alert_id: int, user: str, note: str) -> bool:
        """Добавляет заметку к алерту"""
        alert = self.get_alert(alert_id)
        if not alert:
            return False
        
        alert.add_note(user, note)
        self.logger.info(f"Note added to alert {alert_id} by {user}")
        return True
    
    def check_escalations(self):
        """Проверяет и применяет эскалации"""
        for alert in self.alerts.values():
            if self.lifecycle.should_escalate(alert):
                escalation_action = self.lifecycle.get_escalation_action(alert)
                if escalation_action:
                    self.lifecycle.apply_escalation(alert, escalation_action)
    
    def cleanup_stale_alerts(self, max_age_hours: int = 168):  # 1 неделя
        """Очищает устаревшие алерты"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        stale_alerts = [
            alert_id for alert_id, alert in self.alerts.items()
            if alert.created_at < cutoff_time and alert.status in [AlertStatus.RESOLVED, AlertStatus.CLOSED]
        ]
        
        for alert_id in stale_alerts:
            self._remove_alert(alert_id)
        
        if stale_alerts:
            self.logger.info(f"Cleaned up {len(stale_alerts)} stale alerts")
    
    def _remove_alert(self, alert_id: int):
        """Удаляет алерт из всех индексов"""
        alert = self.alerts.get(alert_id)
        if not alert:
            return
        
        # Удаляем из основного индекса
        del self.alerts[alert_id]
        
        # Удаляем из индекса дедупликации
        if alert.dedup_key in self.alerts_by_dedup:
            del self.alerts_by_dedup[alert.dedup_key]
        
        # Удаляем из группировки
        if alert.group_id:
            group = self.alerts_by_group.get(alert.group_id, [])
            group[:] = [a for a in group if a.id != alert_id]
            if not group:
                del self.alerts_by_group[alert.group_id]
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику менеджера алертов"""
        return {
            **self.stats,
            'total_alerts': len(self.alerts),
            'alerts_by_status': {
                status.value: len(self.get_alerts_by_status(status))
                for status in AlertStatus
            },
            'alerts_by_severity': {
                severity.value: len(self.get_alerts_by_severity(severity))
                for severity in AlertSeverity
            },
            'alerts_by_type': {
                alert_type.value: len(self.get_alerts_by_type(alert_type))
                for alert_type in AlertType
            },
            'groups_count': len(self.alerts_by_group),
            'duplicates_prevented': self.stats['duplicates_prevented']
        }
    
    def export_alerts(self, format: str = "json") -> str:
        """Экспортирует алерты в указанном формате"""
        if format.lower() == "json":
            return json.dumps(
                [alert.to_dict() for alert in self.alerts.values()],
                indent=2,
                ensure_ascii=False
            )
        elif format.lower() == "yaml" and yaml:
            return yaml.dump(
                [alert.to_dict() for alert in self.alerts.values()],
                default_flow_style=False,
                allow_unicode=True
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Глобальный экземпляр менеджера алертов
alert_manager = AlertManager()
