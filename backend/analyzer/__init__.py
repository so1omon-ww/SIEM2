"""
SIEM Analyzer Module

Модуль анализатора для системы SIEM, включающий:
- Движок правил
- Корреляцию событий
- Анализ угроз
- Уведомления
- Управление алертами
"""

from .engine.analyzer_core import AnalyzerCore
from .engine.rule_engine import RuleEngine
from .engine.correlation_engine import CorrelationEngine
from .engine.threat_intelligence import ThreatIntelligenceService
from .engine.notification_service import NotificationService
from .engine.alert_manager import AlertManager
from .engine.rule import Rule, RuleType, RuleSeverity, RuleMatch, RuleAction, RuleSet
from .engine.notification_templates import NotificationTemplate, NotificationTemplateManager, template_manager
from .config import AnalyzerConfig, default_config, create_analyzer_config
from .utils import (
    EventMatcher, TimeWindow, EventAggregator, DeduplicationManager,
    ContextBuilder, ValidationUtils, FileUtils
)

__version__ = "2.0.0"

__all__ = [
    # Основные классы
    "AnalyzerCore",
    "RuleEngine", 
    "CorrelationEngine",
    "ThreatIntelligenceService",
    "NotificationService",
    "AlertManager",
    
    # Модели правил
    "Rule",
    "RuleType", 
    "RuleSeverity",
    "RuleMatch",
    "RuleAction",
    "RuleSet",
    
    # Шаблоны уведомлений
    "NotificationTemplate",
    "NotificationTemplateManager",
    "template_manager",
    
    # Конфигурация
    "AnalyzerConfig",
    "default_config",
    "create_analyzer_config",
    
    # Утилиты
    "EventMatcher",
    "TimeWindow",
    "EventAggregator", 
    "DeduplicationManager",
    "ContextBuilder",
    "ValidationUtils",
    "FileUtils",
]
