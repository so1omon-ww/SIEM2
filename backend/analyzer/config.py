"""
Конфигурация системы анализа SIEM
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AnalyzerConfig:
    """Конфигурация анализатора"""
    
    # Основные настройки
    enabled: bool = True
    debug: bool = False
    log_level: str = "INFO"
    
    # Настройки производительности
    max_concurrent_rules: int = 10
    event_batch_size: int = 100
    processing_interval: int = 30  # секунды
    
    # Настройки правил
    rules_directory: str = "backend/analyzer/rules"
    builtin_rules_enabled: bool = True
    custom_rules_enabled: bool = True
    rule_reload_interval: int = 300  # 5 минут
    
    # Настройки уведомлений
    notifications_enabled: bool = True
    notification_channels: List[str] = field(default_factory=lambda: [
        "agent", "log", "email", "webhook"
    ])
    
    # Настройки корреляции
    correlation_enabled: bool = True
    correlation_window: int = 3600  # 1 час
    max_correlation_events: int = 1000
    
    # Настройки угроз
    threat_intelligence_enabled: bool = True
    threat_sources: List[str] = field(default_factory=lambda: [
        "local", "abuseipdb", "virustotal"
    ])
    
    # Настройки базовой линии
    baseline_enabled: bool = True
    baseline_learning_period: int = 604800  # 7 дней
    baseline_min_samples: int = 100
    
    # Настройки логирования
    log_file: Optional[str] = None
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_rotation: str = "1 day"
    log_retention: str = "30 days"
    
    # Настройки базы данных
    db_connection_timeout: int = 30
    db_query_timeout: int = 60
    db_max_retries: int = 3
    
    # Настройки агентов
    agent_notifications_enabled: bool = True
    agent_notification_timeout: int = 10
    agent_retry_attempts: int = 3
    
    # Настройки email
    email_enabled: bool = False
    email_smtp_server: str = "localhost"
    email_smtp_port: int = 587
    email_username: str = ""
    email_password: str = ""
    email_from: str = "siem@company.com"
    email_to: List[str] = field(default_factory=list)
    email_use_tls: bool = True
    
    # Настройки webhook
    webhook_enabled: bool = False
    webhook_urls: List[str] = field(default_factory=list)
    webhook_timeout: int = 10
    webhook_retry_attempts: int = 3
    
    # Настройки Slack
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#security"
    slack_username: str = "SIEM Bot"
    
    # Настройки Telegram
    telegram_enabled: bool = False
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    
    def __post_init__(self):
        """Пост-инициализация конфигурации"""
        # Установка значений по умолчанию из переменных окружения
        self._load_from_env()
        
        # Валидация конфигурации
        self._validate()
    
    def _load_from_env(self):
        """Загрузка конфигурации из переменных окружения"""
        env_mapping = {
            'SIEM_ANALYZER_ENABLED': 'enabled',
            'SIEM_ANALYZER_DEBUG': 'debug',
            'SIEM_ANALYZER_LOG_LEVEL': 'log_level',
            'SIEM_ANALYZER_MAX_CONCURRENT_RULES': 'max_concurrent_rules',
            'SIEM_ANALYZER_EVENT_BATCH_SIZE': 'event_batch_size',
            'SIEM_ANALYZER_PROCESSING_INTERVAL': 'processing_interval',
            'SIEM_ANALYZER_RULES_DIRECTORY': 'rules_directory',
            'SIEM_ANALYZER_BUILTIN_RULES_ENABLED': 'builtin_rules_enabled',
            'SIEM_ANALYZER_CUSTOM_RULES_ENABLED': 'custom_rules_enabled',
            'SIEM_ANALYZER_RULE_RELOAD_INTERVAL': 'rule_reload_interval',
            'SIEM_ANALYZER_NOTIFICATIONS_ENABLED': 'notifications_enabled',
            'SIEM_ANALYZER_CORRELATION_ENABLED': 'correlation_enabled',
            'SIEM_ANALYZER_CORRELATION_WINDOW': 'correlation_window',
            'SIEM_ANALYZER_THREAT_INTELLIGENCE_ENABLED': 'threat_intelligence_enabled',
            'SIEM_ANALYZER_BASELINE_ENABLED': 'baseline_enabled',
            'SIEM_ANALYZER_BASELINE_LEARNING_PERIOD': 'baseline_learning_period',
            'SIEM_ANALYZER_AGENT_NOTIFICATIONS_ENABLED': 'agent_notifications_enabled',
            'SIEM_ANALYZER_EMAIL_ENABLED': 'email_enabled',
            'SIEM_ANALYZER_EMAIL_SMTP_SERVER': 'email_smtp_server',
            'SIEM_ANALYZER_EMAIL_SMTP_PORT': 'email_smtp_port',
            'SIEM_ANALYZER_EMAIL_USERNAME': 'email_username',
            'SIEM_ANALYZER_EMAIL_PASSWORD': 'email_password',
            'SIEM_ANALYZER_EMAIL_FROM': 'email_from',
            'SIEM_ANALYZER_WEBHOOK_ENABLED': 'webhook_enabled',
            'SIEM_ANALYZER_SLACK_ENABLED': 'slack_enabled',
            'SIEM_ANALYZER_TELEGRAM_ENABLED': 'telegram_enabled',
        }
        
        for env_var, attr_name in env_mapping.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Преобразование типов
                attr_value = getattr(self, attr_name)
                if isinstance(attr_value, bool):
                    setattr(self, attr_name, env_value.lower() in ('true', '1', 'yes', 'on'))
                elif isinstance(attr_value, int):
                    try:
                        setattr(self, attr_name, int(env_value))
                    except ValueError:
                        pass
                elif isinstance(attr_value, list):
                    setattr(self, attr_name, env_value.split(','))
                else:
                    setattr(self, attr_name, env_value)
    
    def _validate(self):
        """Валидация конфигурации"""
        if self.processing_interval < 1:
            self.processing_interval = 1
        
        if self.event_batch_size < 1:
            self.event_batch_size = 1
        
        if self.max_concurrent_rules < 1:
            self.max_concurrent_rules = 1
        
        if self.correlation_window < 60:
            self.correlation_window = 60
        
        if self.baseline_learning_period < 86400:  # 1 день
            self.baseline_learning_period = 86400
        
        # Валидация путей к файлам
        self._validate_paths()
        
        # Валидация каналов уведомлений
        self._validate_notification_channels()
    
    def _validate_paths(self):
        """Валидация путей к файлам и директориям"""
        try:
            rules_path = self.get_rules_path()
            if not rules_path.exists():
                raise FileNotFoundError(f"Rules directory not found: {rules_path}")
            
            # Проверка встроенных правил
            if self.builtin_rules_enabled:
                builtin_path = rules_path / "builtin"
                if not builtin_path.exists():
                    raise FileNotFoundError(f"Builtin rules directory not found: {builtin_path}")
                
                # Проверка наличия хотя бы одного файла правил
                yaml_files = list(builtin_path.glob("*.yaml"))
                if not yaml_files:
                    raise FileNotFoundError(f"No YAML rule files found in: {builtin_path}")
            
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def _validate_notification_channels(self):
        """Валидация каналов уведомлений"""
        valid_channels = ["agent", "log", "email", "webhook", "slack", "telegram"]
        
        for channel in self.notification_channels:
            if channel not in valid_channels:
                raise ValueError(f"Invalid notification channel: {channel}. Valid channels: {valid_channels}")
        
        # Проверка конфигурации email
        if "email" in self.notification_channels and self.email_enabled:
            if not self.email_smtp_server or not self.email_from:
                raise ValueError("Email configuration incomplete: smtp_server and from are required")
        
        # Проверка конфигурации webhook
        if "webhook" in self.notification_channels and self.webhook_enabled:
            if not self.webhook_urls:
                raise ValueError("Webhook configuration incomplete: webhook_urls is required")
        
        # Проверка конфигурации Slack
        if "slack" in self.notification_channels and self.slack_enabled:
            if not self.slack_webhook_url:
                raise ValueError("Slack configuration incomplete: webhook_url is required")
        
        # Проверка конфигурации Telegram
        if "telegram" in self.notification_channels and self.telegram_enabled:
            if not self.telegram_bot_token or not self.telegram_chat_id:
                raise ValueError("Telegram configuration incomplete: bot_token and chat_id are required")
    
    def get_rules_path(self) -> Path:
        """Получить путь к директории правил"""
        return Path(self.rules_directory)
    
    def is_channel_enabled(self, channel: str) -> bool:
        """Проверить, включен ли канал уведомлений"""
        return channel in self.notification_channels
    
    def get_notification_config(self, channel: str) -> Dict[str, Any]:
        """Получить конфигурацию для канала уведомлений"""
        if channel == "email" and self.email_enabled:
            return {
                "smtp_server": self.email_smtp_server,
                "smtp_port": self.email_smtp_port,
                "username": self.email_username,
                "password": self.email_password,
                "from": self.email_from,
                "to": self.email_to,
                "use_tls": self.email_use_tls
            }
        elif channel == "webhook" and self.webhook_enabled:
            return {
                "urls": self.webhook_urls,
                "timeout": self.webhook_timeout,
                "retry_attempts": self.webhook_retry_attempts
            }
        elif channel == "slack" and self.slack_enabled:
            return {
                "webhook_url": self.slack_webhook_url,
                "channel": self.slack_channel,
                "username": self.slack_username
            }
        elif channel == "telegram" and self.telegram_enabled:
            return {
                "bot_token": self.telegram_bot_token,
                "chat_id": self.telegram_chat_id
            }
        elif channel == "agent" and self.agent_notifications_enabled:
            return {
                "timeout": self.agent_notification_timeout,
                "retry_attempts": self.agent_retry_attempts
            }
        else:
            return {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать конфигурацию в словарь"""
        return {
            "enabled": self.enabled,
            "debug": self.debug,
            "log_level": self.log_level,
            "max_concurrent_rules": self.max_concurrent_rules,
            "event_batch_size": self.event_batch_size,
            "processing_interval": self.processing_interval,
            "rules_directory": self.rules_directory,
            "builtin_rules_enabled": self.builtin_rules_enabled,
            "custom_rules_enabled": self.custom_rules_enabled,
            "rule_reload_interval": self.rule_reload_interval,
            "notifications_enabled": self.notifications_enabled,
            "notification_channels": self.notification_channels,
            "correlation_enabled": self.correlation_enabled,
            "correlation_window": self.correlation_window,
            "max_correlation_events": self.max_correlation_events,
            "threat_intelligence_enabled": self.threat_intelligence_enabled,
            "threat_sources": self.threat_sources,
            "baseline_enabled": self.baseline_enabled,
            "baseline_learning_period": self.baseline_learning_period,
            "baseline_min_samples": self.baseline_min_samples,
            "agent_notifications_enabled": self.agent_notifications_enabled,
            "email_enabled": self.email_enabled,
            "webhook_enabled": self.webhook_enabled,
            "slack_enabled": self.slack_enabled,
            "telegram_enabled": self.telegram_enabled
        }


# Глобальная конфигурация по умолчанию
default_config = AnalyzerConfig()

# Функция для создания конфигурации
def create_analyzer_config(**kwargs) -> AnalyzerConfig:
    """Создать конфигурацию анализатора с переданными параметрами"""
    config = AnalyzerConfig()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return config
