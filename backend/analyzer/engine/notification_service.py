"""
Notification Service - Сервис уведомлений для SIEM системы

Отправляет уведомления:
- Агентам о новых алертах
- Администраторам о критических событиях
- Внешним системам через webhooks
- Логирует все уведомления
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import asyncio
import json
import logging
import os
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
except ImportError:
    smtplib = None


class NotificationType(str, Enum):
    """Типы уведомлений"""
    ALERT = "alert"                    # Новый алерт
    THREAT = "threat"                  # Угроза
    ANOMALY = "anomaly"                # Аномалия
    SYSTEM = "system"                  # Системное событие
    MAINTENANCE = "maintenance"         # Обслуживание
    INFO = "info"                      # Информация


class NotificationPriority(str, Enum):
    """Приоритеты уведомлений"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Каналы доставки уведомлений"""
    AGENT = "agent"                    # Уведомление агента
    EMAIL = "email"                    # Email
    WEBHOOK = "webhook"                # HTTP webhook
    SLACK = "slack"                    # Slack
    TELEGRAM = "telegram"              # Telegram
    LOG = "log"                        # Логирование
    DATABASE = "database"              # Сохранение в БД


@dataclass
class NotificationRecipient:
    """Получатель уведомления"""
    id: str
    type: str  # agent, email, webhook, etc.
    address: str  # email, URL, agent_id, etc.
    name: str = ""
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Notification:
    """Уведомление"""
    id: str
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Метаданные
    source: str = "analyzer"
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Временные метки
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    
    # Статус доставки
    status: str = "pending"  # pending, sent, delivered, failed
    retry_count: int = 0
    max_retries: int = 3
    
    # Получатели
    recipients: List[NotificationRecipient] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует уведомление в словарь"""
        return {
            'id': self.id,
            'type': self.type.value,
            'priority': self.priority.value,
            'title': self.title,
            'message': self.message,
            'data': self.data,
            'source': self.source,
            'category': self.category,
            'tags': self.tags,
            'created_at': self.created_at.isoformat(),
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'status': self.status,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'recipients': [
                {
                    'id': r.id,
                    'type': r.type,
                    'address': r.address,
                    'name': r.name,
                    'enabled': r.enabled,
                    'parameters': r.parameters
                } for r in self.recipients
            ]
        }


class NotificationTemplate:
    """Шаблон уведомления"""
    
    def __init__(self, name: str, template: str, variables: List[str] = None):
        self.name = name
        self.template = template
        self.variables = variables or []
    
    def render(self, **kwargs) -> str:
        """Рендерит шаблон с переданными переменными"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            missing_var = str(e).strip("'")
            return f"Template error: missing variable {missing_var}"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NotificationTemplate':
        """Создает шаблон из словаря"""
        return cls(
            name=data['name'],
            template=data['template'],
            variables=data.get('variables', [])
        )


class NotificationService:
    """Основной сервис уведомлений"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger("notification_service")
        self.config = self._load_config_from_object(config) if config else self._load_config()
        self.templates = self._load_templates()
        self.recipients = self._load_recipients()
        self.delivery_queue = asyncio.Queue()
        self.is_running = False
        
        # Статистика
        self.stats = {
            'sent': 0,
            'delivered': 0,
            'failed': 0,
            'total': 0
        }
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Загружает конфигурацию"""
        default_config = {
            'retry_delay': 5,  # секунды
            'max_retries': 3,
            'batch_size': 10,
            'delivery_timeout': 30,
            'enable_logging': True,
            'enable_database': True,
            'channels': {
                'agent': {'enabled': True},
                'email': {'enabled': False},
                'webhook': {'enabled': False},
                'slack': {'enabled': False},
                'telegram': {'enabled': False}
            }
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
    
    def _load_config_from_object(self, config) -> Dict[str, Any]:
        """Загружает конфигурацию из объекта конфигурации"""
        if hasattr(config, '__dict__'):
            return config.__dict__
        elif isinstance(config, dict):
            return config
        else:
            return {}
    
    def _load_templates(self) -> Dict[str, NotificationTemplate]:
        """Загружает шаблоны уведомлений"""
        templates = {}
        
        # Встроенные шаблоны
        builtin_templates = {
            'alert_new': NotificationTemplate(
                name='alert_new',
                template='[ALERT] New alert: {title}\n\n{description}\n\nSource: {source}\nSeverity: {severity}',
                variables=['title', 'description', 'source', 'severity']
            ),
            'threat_detected': NotificationTemplate(
                name='threat_detected',
                template='[WARNING] Обнаружена угроза!\n\n{description}\n\nIP: {ip}\nПорт: {port}\nПротокол: {protocol}',
                variables=['description', 'ip', 'port', 'protocol']
            ),
            'anomaly_detected': NotificationTemplate(
                name='anomaly_detected',
                template='🔍 Обнаружена аномалия\n\n{description}\n\nЗначение: {value}\nПорог: {threshold}',
                variables=['description', 'value', 'threshold']
            ),
            'system_event': NotificationTemplate(
                name='system_event',
                template='[INFO] Системное событие\n\n{message}\n\nКомпонент: {component}\nСтатус: {status}',
                variables=['message', 'component', 'status']
            )
        }
        
        templates.update(builtin_templates)
        
        # Загружаем пользовательские шаблоны
        templates_dir = Path(__file__).parent.parent / "templates"
        if templates_dir.exists():
            for template_file in templates_dir.glob("*.yaml"):
                try:
                    if yaml:
                        with open(template_file, 'r', encoding='utf-8') as f:
                            template_data = yaml.safe_load(f)
                            if isinstance(template_data, dict):
                                template = NotificationTemplate.from_dict(template_data)
                                templates[template.name] = template
                except Exception as e:
                    self.logger.error(f"Failed to load template {template_file}: {e}")
        
        return templates
    
    def _load_recipients(self) -> List[NotificationRecipient]:
        """Загружает получателей уведомлений"""
        recipients = []
        
        # Загружаем из конфигурации
        if 'recipients' in self.config:
            for recipient_data in self.config['recipients']:
                try:
                    recipient = NotificationRecipient(**recipient_data)
                    recipients.append(recipient)
                except Exception as e:
                    self.logger.error(f"Failed to load recipient: {e}")
        
        # Загружаем из файла
        recipients_file = Path(__file__).parent.parent / "recipients.yaml"
        if recipients_file.exists() and yaml:
            try:
                with open(recipients_file, 'r', encoding='utf-8') as f:
                    recipients_data = yaml.safe_load(f) or {}
                    for recipient_data in recipients_data.get('recipients', []):
                        try:
                            recipient = NotificationRecipient(**recipient_data)
                            recipients.append(recipient)
                        except Exception as e:
                            self.logger.error(f"Failed to load recipient from file: {e}")
            except Exception as e:
                self.logger.error(f"Failed to load recipients file: {e}")
        
        return recipients
    
    async def start(self):
        """Запускает сервис уведомлений"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Notification service started")
        
        # Запускаем обработчик очереди
        asyncio.create_task(self._delivery_worker())
    
    async def stop(self):
        """Останавливает сервис уведомлений"""
        self.is_running = False
        self.logger.info("Notification service stopped")
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        priority: NotificationPriority,
        title: str,
        message: str,
        data: Dict[str, Any] = None,
        recipients: List[str] = None,
        template: str = None,
        **kwargs
    ) -> str:
        """Отправляет уведомление"""
        notification_id = f"{notification_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(title)}"
        
        # Рендерим сообщение из шаблона
        if template and template in self.templates:
            template_obj = self.templates[template]
            message = template_obj.render(**kwargs)
        
        # Создаем уведомление
        notification = Notification(
            id=notification_id,
            type=notification_type,
            priority=priority,
            title=title,
            message=message,
            data=data or {},
            **kwargs
        )
        
        # Добавляем получателей
        if recipients:
            for recipient_id in recipients:
                recipient = self._get_recipient(recipient_id)
                if recipient:
                    notification.recipients.append(recipient)
        else:
            # Добавляем всех активных получателей по умолчанию
            notification.recipients.extend([r for r in self.recipients if r.enabled])
        
        # Добавляем в очередь доставки
        await self.delivery_queue.put(notification)
        self.stats['total'] += 1
        
        self.logger.info(f"Notification queued: {notification_id} - {title}")
        return notification_id
    
    def _get_recipient(self, recipient_id: str) -> Optional[NotificationRecipient]:
        """Получает получателя по ID"""
        for recipient in self.recipients:
            if recipient.id == recipient_id:
                return recipient
        return None
    
    async def _delivery_worker(self):
        """Рабочий процесс для доставки уведомлений"""
        while self.is_running:
            try:
                # Получаем уведомление из очереди
                notification = await asyncio.wait_for(
                    self.delivery_queue.get(), 
                    timeout=1.0
                )
                
                # Доставляем уведомление
                await self._deliver_notification(notification)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Delivery worker error: {e}")
    
    async def _deliver_notification(self, notification: Notification):
        """Доставляет уведомление получателям"""
        delivery_tasks = []
        
        for recipient in notification.recipients:
            if not recipient.enabled:
                continue
            
            # Создаем задачу доставки
            task = asyncio.create_task(
                self._deliver_to_recipient(notification, recipient)
            )
            delivery_tasks.append(task)
        
        # Ждем завершения всех задач доставки
        if delivery_tasks:
            results = await asyncio.gather(*delivery_tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    self.logger.error(f"Delivery failed to {delivery_tasks[i]}: {result}")
                    notification.status = "failed"
                    self.stats['failed'] += 1
                else:
                    notification.status = "delivered"
                    self.stats['delivered'] += 1
    
    async def _deliver_to_recipient(self, notification: Notification, recipient: NotificationRecipient):
        """Доставляет уведомление конкретному получателю"""
        try:
            if recipient.type == NotificationChannel.AGENT:
                await self._deliver_to_agent(notification, recipient)
            elif recipient.type == NotificationChannel.EMAIL:
                await self._deliver_to_email(notification, recipient)
            elif recipient.type == NotificationChannel.WEBHOOK:
                await self._deliver_to_webhook(notification, recipient)
            elif recipient.type == NotificationChannel.SLACK:
                await self._deliver_to_slack(notification, recipient)
            elif recipient.type == NotificationChannel.TELEGRAM:
                await self._deliver_to_telegram(notification, recipient)
            elif recipient.type == NotificationChannel.LOG:
                await self._deliver_to_log(notification, recipient)
            elif recipient.type == NotificationChannel.DATABASE:
                await self._deliver_to_database(notification, recipient)
            else:
                self.logger.warning(f"Unknown delivery channel: {recipient.type}")
                
        except Exception as e:
            self.logger.error(f"Delivery to {recipient.type} failed: {e}")
            raise
    
    async def _deliver_to_agent(self, notification: Notification, recipient: NotificationRecipient):
        """Доставляет уведомление агенту"""
        # Здесь должна быть логика отправки уведомления агенту
        # Например, через WebSocket, HTTP API или очередь сообщений
        
        agent_id = recipient.address
        notification_data = {
            'type': 'notification',
            'notification': notification.to_dict(),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Логируем для отладки
        self.logger.info(f"Notification sent to agent {agent_id}: {notification.title}")
        
        # TODO: Реализовать реальную отправку агенту
        # await self._send_to_agent(agent_id, notification_data)
    
    async def _deliver_to_email(self, notification: Notification, recipient: NotificationRecipient):
        """Доставляет уведомление по email"""
        if not smtplib:
            raise RuntimeError("SMTP support not available")
        
        # TODO: Реализовать отправку email
        self.logger.info(f"Email notification sent to {recipient.address}")
    
    async def _deliver_to_webhook(self, notification: Notification, recipient: NotificationRecipient):
        """Доставляет уведомление через webhook"""
        if not aiohttp:
            raise RuntimeError("aiohttp support not available")
        
        webhook_url = recipient.address
        notification_data = notification.to_dict()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=notification_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status >= 400:
                        raise Exception(f"Webhook returned status {response.status}")
                    
                    self.logger.info(f"Webhook notification sent to {webhook_url}")
                    
        except Exception as e:
            self.logger.error(f"Webhook delivery failed: {e}")
            raise
    
    async def _deliver_to_slack(self, notification: Notification, recipient: NotificationRecipient):
        """Доставляет уведомление в Slack"""
        # TODO: Реализовать интеграцию со Slack
        self.logger.info(f"Slack notification sent to {recipient.address}")
    
    async def _deliver_to_telegram(self, notification: Notification, recipient: NotificationRecipient):
        """Доставляет уведомление в Telegram"""
        # TODO: Реализовать интеграцию с Telegram
        self.logger.info(f"Telegram notification sent to {recipient.address}")
    
    async def _deliver_to_log(self, notification: Notification, recipient: NotificationRecipient):
        """Логирует уведомление"""
        log_level = getattr(logging, notification.priority.upper(), logging.INFO)
        self.logger.log(
            log_level,
            f"NOTIFICATION [{notification.type.value.upper()}] {notification.title}: {notification.message}"
        )
    
    async def _deliver_to_database(self, notification: Notification, recipient: NotificationRecipient):
        """Сохраняет уведомление в базу данных"""
        # TODO: Реализовать сохранение в БД
        self.logger.info(f"Notification saved to database: {notification.id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику сервиса"""
        return {
            **self.stats,
            'queue_size': self.delivery_queue.qsize(),
            'is_running': self.is_running,
            'recipients_count': len(self.recipients),
            'templates_count': len(self.templates)
        }
    
    def add_recipient(self, recipient: NotificationRecipient):
        """Добавляет нового получателя"""
        self.recipients.append(recipient)
        self.logger.info(f"Added recipient: {recipient.id} ({recipient.type})")
    
    def remove_recipient(self, recipient_id: str):
        """Удаляет получателя"""
        self.recipients = [r for r in self.recipients if r.id != recipient_id]
        self.logger.info(f"Removed recipient: {recipient_id}")
    
    def add_template(self, template: NotificationTemplate):
        """Добавляет новый шаблон"""
        self.templates[template.name] = template
        self.logger.info(f"Added template: {template.name}")
    
    def remove_template(self, template_name: str):
        """Удаляет шаблон"""
        if template_name in self.templates:
            del self.templates[template_name]
            self.logger.info(f"Removed template: {template_name}")


# Глобальный экземпляр сервиса
notification_service = NotificationService()


async def send_notification(
    notification_type: NotificationType,
    priority: NotificationPriority,
    title: str,
    message: str,
    **kwargs
) -> str:
    """Удобная функция для отправки уведомлений"""
    return await notification_service.send_notification(
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        **kwargs
    )


async def send_alert_notification(
    alert_id: int,
    title: str,
    description: str,
    severity: str,
    source: str,
    **kwargs
) -> str:
    """Отправляет уведомление о новом алерте"""
    return await send_notification(
        notification_type=NotificationType.ALERT,
        priority=NotificationPriority.HIGH if severity in ['high', 'critical'] else NotificationPriority.NORMAL,
        title=f"[ALERT] {title}",
        message=description,
        template='alert_new',
        alert_id=alert_id,
        severity=severity,
        source=source,
        **kwargs
    )


async def send_threat_notification(
    threat_type: str,
    description: str,
    ip: str = None,
    port: int = None,
    protocol: str = None,
    **kwargs
) -> str:
    """Отправляет уведомление об угрозе"""
    return await send_notification(
        notification_type=NotificationType.THREAT,
        priority=NotificationPriority.CRITICAL,
        title=f"[WARNING] Обнаружена угроза: {threat_type}",
        message=description,
        template='threat_detected',
        threat_type=threat_type,
        ip=ip,
        port=port,
        protocol=protocol,
        **kwargs
    )
