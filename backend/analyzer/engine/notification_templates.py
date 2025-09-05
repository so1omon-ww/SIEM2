"""
Шаблоны уведомлений для системы анализа
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TemplateType(Enum):
    """Типы шаблонов уведомлений"""
    THREAT_DETECTED = "threat_detected"
    ANOMALY_DETECTED = "anomaly_detected"
    CRITICAL_PROCESS = "critical_process"
    SUSPICIOUS_NETWORK = "suspicious_network"
    AUTH_FAILURE = "auth_failure"
    USER_ANOMALY = "user_anomaly"
    PORT_SCAN = "port_scan"
    BRUTE_FORCE = "brute_force"
    LATERAL_MOVEMENT = "lateral_movement"
    GENERAL_ALERT = "general_alert"


@dataclass
class NotificationTemplate:
    """Шаблон уведомления"""
    name: str
    title_template: str
    message_template: str
    priority: int = 3
    icon: str = "🔔"
    color: str = "default"
    channels: list = None
    
    def __post_init__(self):
        if self.channels is None:
            self.channels = ["agent", "log"]


class NotificationTemplateManager:
    """Менеджер шаблонов уведомлений"""
    
    def __init__(self):
        self._templates: Dict[str, NotificationTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Загрузка стандартных шаблонов"""
        default_templates = [
            NotificationTemplate(
                name="threat_detected",
                title_template="Threat detected",
                message_template="Обнаружена угроза безопасности: {description}",
                priority=1,
                icon="[ALERT]",
                color="red",
                channels=["agent", "email", "webhook", "log"]
            ),
            
            NotificationTemplate(
                name="anomaly_detected",
                title_template="[WARNING] Аномалия обнаружена",
                message_template="Обнаружена аномалия в системе: {description}",
                priority=2,
                icon="[WARNING]",
                color="yellow",
                channels=["agent", "email", "log"]
            ),
            
            NotificationTemplate(
                name="critical_process",
                title_template="Critical process",
                message_template="Запущен критический процесс: {process_name} с IP {src_ip}",
                priority=1,
                icon="[ALERT]",
                color="red",
                channels=["agent", "email", "webhook", "slack", "log"]
            ),
            
            NotificationTemplate(
                name="suspicious_network",
                title_template="[WARNING] Подозрительная сеть",
                message_template="Обнаружена подозрительная сетевая активность: {description}",
                priority=2,
                icon="[WARNING]",
                color="orange",
                channels=["agent", "email", "log"]
            ),
            
            NotificationTemplate(
                name="auth_failure",
                title_template="🔒 Неудачная аутентификация",
                message_template="Обнаружены неудачные попытки входа: {description}",
                priority=2,
                icon="🔒",
                color="orange",
                channels=["agent", "email", "log"]
            ),
            
            NotificationTemplate(
                name="user_anomaly",
                title_template="👤 Аномалия пользователя",
                message_template="Обнаружена аномалия в поведении пользователя: {description}",
                priority=1,
                icon="👤",
                color="red",
                channels=["agent", "email", "webhook", "log"]
            ),
            
            NotificationTemplate(
                name="port_scan",
                title_template="🔍 Сканирование портов",
                message_template="Обнаружено сканирование портов с {src_ip} на {dst_ip}",
                priority=2,
                icon="🔍",
                color="orange",
                channels=["agent", "email", "log"]
            ),
            
            NotificationTemplate(
                name="brute_force",
                title_template="💥 Брутфорс атака",
                message_template="Обнаружена брутфорс атака: {description}",
                priority=1,
                icon="💥",
                color="red",
                channels=["agent", "email", "webhook", "slack", "log"]
            ),
            
            NotificationTemplate(
                name="lateral_movement",
                title_template="🔄 Латеральное движение",
                message_template="Обнаружены признаки латерального движения: {description}",
                priority=1,
                icon="🔄",
                color="red",
                channels=["agent", "email", "webhook", "log"]
            ),
            
            NotificationTemplate(
                name="general_alert",
                title_template="🔔 Уведомление",
                message_template="{message}",
                priority=3,
                icon="🔔",
                color="blue",
                channels=["agent", "log"]
            )
        ]
        
        for template in default_templates:
            self._templates[template.name] = template
    
    def get_template(self, name: str) -> Optional[NotificationTemplate]:
        """Получить шаблон по имени"""
        return self._templates.get(name)
    
    def add_template(self, template: NotificationTemplate):
        """Добавить новый шаблон"""
        self._templates[template.name] = template
    
    def remove_template(self, name: str) -> bool:
        """Удалить шаблон"""
        if name in self._templates:
            del self._templates[name]
            return True
        return False
    
    def list_templates(self) -> list:
        """Список всех шаблонов"""
        return list(self._templates.keys())
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Рендеринг шаблона с контекстом"""
        template = self.get_template(template_name)
        if not template:
            return None
        
        try:
            title = template.title_template.format(**context)
            message = template.message_template.format(**context)
            
            return {
                "title": title,
                "message": message,
                "priority": template.priority,
                "icon": template.icon,
                "color": template.color,
                "channels": template.channels
            }
        except KeyError as e:
            # Если не хватает переменных в контексте, используем fallback
            fallback_context = {
                "description": context.get("description", "Событие безопасности"),
                "message": context.get("message", "Обнаружено событие безопасности"),
                "src_ip": context.get("src_ip", "неизвестно"),
                "dst_ip": context.get("dst_ip", "неизвестно"),
                "process_name": context.get("process_name", "неизвестно"),
                "username": context.get("username", "неизвестно"),
                "count": context.get("count", "несколько"),
                **context
            }
            
            try:
                title = template.title_template.format(**fallback_context)
                message = template.message_template.format(**fallback_context)
                
                return {
                    "title": title,
                    "message": message,
                    "priority": template.priority,
                    "icon": template.icon,
                    "color": template.color,
                    "channels": template.channels
                }
            except:
                # Если и fallback не работает, возвращаем базовое уведомление
                return {
                    "title": f"{template.icon} Уведомление",
                    "message": f"Событие: {context.get('event_type', 'неизвестно')}",
                    "priority": template.priority,
                    "icon": template.icon,
                    "color": template.color,
                    "channels": template.channels
                }


# Глобальный экземпляр менеджера шаблонов
template_manager = NotificationTemplateManager()
