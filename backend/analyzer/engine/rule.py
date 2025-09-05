"""
Rule Models - Модели правил для аналитического движка

Поддерживает:
- Immediate rules: Мгновенное срабатывание
- Threshold rules: Правила с порогами
- Correlation rules: Корреляция событий
- Complex conditions: Сложные условия
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import re
import json


class RuleType(str, Enum):
    """Типы правил"""
    IMMEDIATE = "immediate"      # Мгновенное срабатывание
    THRESHOLD = "threshold"      # Правило с порогом
    CORRELATION = "correlation"  # Корреляция событий
    BASELINE = "baseline"        # Базовые показатели
    ANOMALY = "anomaly"          # Аномалии


class RuleSeverity(str, Enum):
    """Уровни важности правил"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RuleStatus(str, Enum):
    """Статусы правил"""
    ACTIVE = "active"
    DISABLED = "disabled"
    TESTING = "testing"
    DEPRECATED = "deprecated"


@dataclass
class RuleMatch:
    """Условия для срабатывания правила"""
    field: str
    operator: str  # eq, ne, gt, lt, gte, lte, in, not_in, regex, exists
    value: Any
    case_sensitive: bool = True
    
    def __post_init__(self):
        if self.operator not in ["eq", "ne", "gt", "lt", "gte", "lte", "in", "not_in", "regex", "exists"]:
            raise ValueError(f"Invalid operator: {self.operator}")


@dataclass
class RuleAction:
    """Действие при срабатывании правила"""
    type: str  # alert, notification, block, log, script
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1


@dataclass
class Rule:
    """Правило анализа событий"""
    # Основные параметры
    name: str
    type: RuleType
    description: str = ""
    version: str = "1.0"
    status: RuleStatus = RuleStatus.ACTIVE
    
    # Условия срабатывания
    matches: List[RuleMatch] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Настройки важности и группировки
    severity: RuleSeverity = RuleSeverity.MEDIUM
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # Настройки для threshold правил
    window: Optional[str] = None  # 5m, 1h, 1d
    threshold: Optional[int] = None
    group_by: Optional[List[str]] = None
    dedup_key: Optional[str] = None
    
    # Действия
    actions: List[RuleAction] = field(default_factory=list)
    
    # Метаданные
    author: str = "system"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Настройки производительности
    enabled: bool = True
    priority: int = 100
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Валидация для threshold правил
        if self.type == RuleType.THRESHOLD:
            if not self.window or not self.threshold:
                raise ValueError("Threshold rules require window and threshold")
        
        # Валидация для correlation правил
        if self.type == RuleType.CORRELATION:
            if not self.conditions:
                raise ValueError("Correlation rules require conditions")
    
    @property
    def window_timedelta(self) -> Optional[timedelta]:
        """Преобразует строку окна в timedelta"""
        if not self.window:
            return None
        
        return self._parse_window(self.window)
    
    @staticmethod
    def _parse_window(window_str: str) -> timedelta:
        """Парсит строку окна времени"""
        pattern = r"(\d+)\s*([smhdwy])"
        match = re.match(pattern, window_str.lower())
        if not match:
            raise ValueError(f"Invalid window format: {window_str}")
        
        value, unit = int(match.group(1)), match.group(2)
        units = {
            's': timedelta(seconds=value),
            'm': timedelta(minutes=value),
            'h': timedelta(hours=value),
            'd': timedelta(days=value),
            'w': timedelta(weeks=value),
            'y': timedelta(days=value * 365)
        }
        return units[unit]
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует правило в словарь"""
        return {
            'name': self.name,
            'type': self.type.value,
            'description': self.description,
            'version': self.version,
            'status': self.status.value,
            'matches': [
                {
                    'field': m.field,
                    'operator': m.operator,
                    'value': m.value,
                    'case_sensitive': m.case_sensitive
                } for m in self.matches
            ],
            'conditions': self.conditions,
            'severity': self.severity.value,
            'category': self.category,
            'tags': self.tags,
            'window': self.window,
            'threshold': self.threshold,
            'group_by': self.group_by,
            'dedup_key': self.dedup_key,
            'actions': [
                {
                    'type': a.type,
                    'parameters': a.parameters,
                    'priority': a.priority
                } for a in self.actions
            ],
            'author': self.author,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'enabled': self.enabled,
            'priority': self.priority
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Rule':
        """Создает правило из словаря"""
        # Преобразуем enum значения
        data['type'] = RuleType(data['type'])
        data['severity'] = RuleSeverity(data['severity'])
        data['status'] = RuleStatus(data.get('status', 'active'))  # Значение по умолчанию
        
        # Преобразуем matches
        if 'matches' in data:
            data['matches'] = [
                RuleMatch(**match_data) for match_data in data['matches']
            ]
        
        # Преобразуем actions
        if 'actions' in data:
            data['actions'] = [
                RuleAction(**action_data) for action_data in data['actions']
            ]
        
        # Преобразуем даты
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        
        return cls(**data)
    
    def is_active(self) -> bool:
        """Проверяет, активно ли правило"""
        return self.enabled and self.status == RuleStatus.ACTIVE
    
    def matches_event(self, event: Dict[str, Any]) -> bool:
        """Проверяет, соответствует ли событие правилу"""
        if not self.is_active():
            return False
        
        # Проверяем все условия matches
        for match in self.matches:
            if not self._evaluate_match(event, match):
                return False
        
        # Проверяем дополнительные условия
        if self.conditions:
            if not self._evaluate_conditions(event, self.conditions):
                return False
        
        return True
    
    def _evaluate_match(self, event: Dict[str, Any], match: RuleMatch) -> bool:
        """Оценивает одно условие matches"""
        field_value = self._get_field_value(event, match.field)
        
        if match.operator == "exists":
            return field_value is not None
        
        if field_value is None:
            return False
        
        if match.operator == "eq":
            return field_value == match.value
        elif match.operator == "ne":
            return field_value != match.value
        elif match.operator == "gt":
            return field_value > match.value
        elif match.operator == "lt":
            return field_value < match.value
        elif match.operator == "gte":
            return field_value >= match.value
        elif match.operator == "lte":
            return field_value <= match.value
        elif match.operator == "in":
            return field_value in match.value
        elif match.operator == "not_in":
            return field_value not in match.value
        elif match.operator == "regex":
            if not isinstance(field_value, str):
                return False
            flags = 0 if match.case_sensitive else re.IGNORECASE
            return bool(re.search(match.value, field_value, flags))
        
        return False
    
    def _evaluate_conditions(self, event: Dict[str, Any], conditions: Dict[str, Any]) -> bool:
        """Оценивает сложные условия"""
        # Простая реализация - можно расширить для поддержки AND/OR логики
        for field, condition in conditions.items():
            if not self._evaluate_condition(event, field, condition):
                return False
        return True
    
    def _evaluate_condition(self, event: Dict[str, Any], field: str, condition: Any) -> bool:
        """Оценивает одно условие"""
        field_value = self._get_field_value(event, field)
        
        if isinstance(condition, dict):
            # Поддержка операторов в условиях
            for op, value in condition.items():
                if op == "eq":
                    return field_value == value
                elif op == "ne":
                    return field_value != value
                elif op == "gt":
                    return field_value > value
                elif op == "lt":
                    return field_value < value
                elif op == "in":
                    return field_value in value
                elif op == "regex":
                    if not isinstance(field_value, str):
                        return False
                    return bool(re.search(value, field_value))
        else:
            # Простое сравнение
            return field_value == condition
        
        return False
    
    def _get_field_value(self, event: Dict[str, Any], field_path: str) -> Any:
        """Получает значение поля из события по пути (например, 'details.src_ip')"""
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


class RuleSet:
    """Набор правил с возможностью загрузки из YAML"""
    
    def __init__(self, rules: List[Rule] = None):
        self.rules = rules or []
        self._rules_by_name = {rule.name: rule for rule in self.rules}
        self._rules_by_type = {}
        self._rules_by_category = {}
        self._update_indexes()
    
    def _update_indexes(self):
        """Обновляет индексы для быстрого поиска"""
        self._rules_by_name = {rule.name: rule for rule in self.rules}
        
        # Группировка по типу
        self._rules_by_type = {}
        for rule in self.rules:
            if rule.type not in self._rules_by_type:
                self._rules_by_type[rule.type] = []
            self._rules_by_type[rule.type].append(rule)
        
        # Группировка по категории
        self._rules_by_category = {}
        for rule in self.rules:
            if rule.category not in self._rules_by_category:
                self._rules_by_category[rule.category] = []
            self._rules_by_category[rule.category].append(rule)
    
    def add_rule(self, rule: Rule):
        """Добавляет правило в набор"""
        self.rules.append(rule)
        self._update_indexes()
    
    def remove_rule(self, rule_name: str):
        """Удаляет правило по имени"""
        self.rules = [r for r in self.rules if r.name != rule_name]
        self._update_indexes()
    
    def get_rule(self, name: str) -> Optional[Rule]:
        """Получает правило по имени"""
        return self._rules_by_name.get(name)
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Получает правила по типу"""
        return self._rules_by_type.get(rule_type, [])
    
    def get_rules_by_category(self, category: str) -> List[Rule]:
        """Получает правила по категории"""
        return self._rules_by_category.get(category, [])
    
    def get_active_rules(self) -> List[Rule]:
        """Получает все активные правила"""
        return [rule for rule in self.rules if rule.is_active()]
    
    def filter_rules(self, **kwargs) -> List[Rule]:
        """Фильтрует правила по параметрам"""
        filtered = self.rules
        
        if 'type' in kwargs:
            filtered = [r for r in filtered if r.type == kwargs['type']]
        
        if 'severity' in kwargs:
            filtered = [r for r in filtered if r.severity == kwargs['severity']]
        
        if 'category' in kwargs:
            filtered = [r for r in filtered if r.category == kwargs['category']]
        
        if 'enabled' in kwargs:
            filtered = [r for r in filtered if r.enabled == kwargs['enabled']]
        
        return filtered
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует набор правил в словарь"""
        return {
            'rules': [rule.to_dict() for rule in self.rules],
            'total_count': len(self.rules),
            'active_count': len(self.get_active_rules())
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RuleSet':
        """Создает набор правил из словаря"""
        rules = []
        if 'rules' in data:
            rules = [Rule.from_dict(rule_data) for rule_data in data['rules']]
        return cls(rules)
