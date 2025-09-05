"""
Correlation Engine - Движок корреляции событий для SIEM системы

Функциональность:
- Выявление связей между событиями
- Временная корреляция
- Пространственная корреляция
- Корреляция по атрибутам
- Машинное обучение для выявления паттернов
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
import asyncio
import json
import logging
import math
from collections import defaultdict, deque
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


class CorrelationType(str, Enum):
    """Типы корреляции"""
    TEMPORAL = "temporal"          # Временная корреляция
    SPATIAL = "spatial"            # Пространственная корреляция
    ATTRIBUTE = "attribute"        # Корреляция по атрибутам
    BEHAVIORAL = "behavioral"      # Поведенческая корреляция
    STATISTICAL = "statistical"    # Статистическая корреляция
    ML_BASED = "ml_based"          # На основе машинного обучения


class CorrelationStrength(str, Enum):
    """Сила корреляции"""
    WEAK = "weak"                  # Слабая корреляция
    MODERATE = "moderate"          # Умеренная корреляция
    STRONG = "strong"              # Сильная корреляция
    VERY_STRONG = "very_strong"    # Очень сильная корреляция


@dataclass
class CorrelationRule:
    """Правило корреляции"""
    name: str
    description: str = ""
    correlation_type: CorrelationType = CorrelationType.TEMPORAL
    
    # Условия корреляции
    min_events: int = 2
    max_events: int = 100
    time_window: int = 3600  # секунды
    spatial_threshold: float = 0.1  # для пространственной корреляции
    
    # Атрибуты для корреляции
    correlation_fields: List[str] = field(default_factory=list)
    exclude_fields: List[str] = field(default_factory=list)
    
    # Настройки
    enabled: bool = True
    priority: int = 100
    confidence_threshold: float = 0.7
    
    # Метаданные
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = self.created_at


@dataclass
class CorrelationResult:
    """Результат корреляции"""
    rule_name: str
    correlation_type: CorrelationType
    strength: CorrelationStrength
    confidence: float
    
    # События в корреляции
    events: List[Dict[str, Any]]
    event_count: int
    
    # Метаданные
    correlation_id: str
    created_at: datetime
    time_span: float  # секунды
    spatial_distance: Optional[float] = None
    
    # Дополнительные данные
    attributes: Dict[str, Any] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует результат корреляции в словарь"""
        return {
            'rule_name': self.rule_name,
            'correlation_type': self.correlation_type.value,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'events': [e.get('id') for e in self.events if e.get('id')],
            'event_count': self.event_count,
            'correlation_id': self.correlation_id,
            'created_at': self.created_at.isoformat(),
            'time_span': self.time_span,
            'spatial_distance': self.spatial_distance,
            'attributes': self.attributes,
            'patterns': self.patterns
        }


class CorrelationEngine:
    """Движок корреляции событий"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger("correlation_engine")
        self.config = self._load_config_from_object(config) if config else self._load_config()
        
        # Правила корреляции
        self.correlation_rules: List[CorrelationRule] = []
        
        # Кэши и индексы
        self.event_cache: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.correlation_cache: Dict[str, List[CorrelationResult]] = defaultdict(list)
        self.pattern_cache: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Статистика
        self.stats = {
            'correlations_found': 0,
            'rules_processed': 0,
            'events_analyzed': 0,
            'patterns_detected': 0
        }
        
        # Состояние
        self.is_running = False
        
        # Загружаем правила корреляции
        self._load_correlation_rules()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Загружает конфигурацию движка корреляции"""
        default_config = {
            'enable_temporal_correlation': True,
            'enable_spatial_correlation': True,
            'enable_attribute_correlation': True,
            'enable_behavioral_correlation': True,
            'enable_ml_correlation': False,
            'max_correlation_window': 86400,  # 24 часа
            'min_correlation_confidence': 0.5,
            'correlation_check_interval': 30,  # 30 секунд
            'max_patterns_per_rule': 10,
            'enable_auto_correlation': True
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
    
    def _load_correlation_rules(self):
        """Загружает правила корреляции"""
        rules_dir = Path(__file__).parent.parent / "rules" / "correlation"
        
        if not rules_dir.exists():
            self.logger.warning(f"Correlation rules directory not found: {rules_dir}")
            return
        
        loaded_rules = []
        
        for rule_file in rules_dir.glob("*.yaml"):
            try:
                with open(rule_file, 'r', encoding='utf-8') as f:
                    if yaml:
                        data = yaml.safe_load(f) or {}
                    else:
                        data = json.load(f)
                    
                    if isinstance(data, dict):
                        if 'rules' in data:
                            # Набор правил
                            for rule_data in data['rules']:
                                try:
                                    rule = CorrelationRule(**rule_data)
                                    loaded_rules.append(rule)
                                except Exception as e:
                                    self.logger.error(f"Failed to load correlation rule from {rule_file}: {e}")
                        else:
                            # Одиночное правило
                            try:
                                rule = CorrelationRule(**data)
                                loaded_rules.append(rule)
                            except Exception as e:
                                self.logger.error(f"Failed to load correlation rule from {rule_file}: {e}")
                    elif isinstance(data, list):
                        # Список правил
                        for rule_data in data:
                            try:
                                rule = CorrelationRule(**rule_data)
                                loaded_rules.append(rule)
                            except Exception as e:
                                self.logger.error(f"Failed to load correlation rule from {rule_file}: {e}")
                    
            except Exception as e:
                self.logger.error(f"Failed to load correlation rule file {rule_file}: {e}")
        
        self.correlation_rules = loaded_rules
        self.logger.info(f"Loaded {len(loaded_rules)} correlation rules")
    
    async def start(self):
        """Запускает движок корреляции"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Correlation engine started")
        
        # Запускаем обработчик корреляции
        asyncio.create_task(self._correlation_processor())
    
    async def stop(self):
        """Останавливает движок корреляции"""
        self.is_running = False
        self.logger.info("Correlation engine stopped")
    
    async def add_event(self, event: Dict[str, Any]):
        """Добавляет событие для анализа корреляции"""
        try:
            # Добавляем событие в кэш
            event_key = self._create_event_key(event)
            self.event_cache[event_key].append({
                'event': event,
                'timestamp': datetime.now(timezone.utc)
            })
            
            # Обновляем статистику
            self.stats['events_analyzed'] += 1
            
        except Exception as e:
            self.logger.error(f"Failed to add event for correlation: {e}")
    
    def _create_event_key(self, event: Dict[str, Any]) -> str:
        """Создает ключ для группировки событий"""
        # Простая группировка по типу события и IP
        event_type = event.get('event_type', 'unknown')
        src_ip = event.get('src_ip', 'unknown')
        dst_ip = event.get('dst_ip', 'unknown')
        
        return f"{event_type}:{src_ip}:{dst_ip}"
    
    async def _correlation_processor(self):
        """Основной процессор корреляции"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['correlation_check_interval'])
                
                # Проверяем все правила корреляции
                for rule in self.correlation_rules:
                    if not rule.enabled:
                        continue
                    
                    try:
                        await self._check_correlation_rule(rule)
                        self.stats['rules_processed'] += 1
                    except Exception as e:
                        self.logger.error(f"Failed to check correlation rule {rule.name}: {e}")
                
            except Exception as e:
                self.logger.error(f"Correlation processor error: {e}")
    
    async def _check_correlation_rule(self, rule: CorrelationRule):
        """Проверяет правило корреляции"""
        try:
            if rule.correlation_type == CorrelationType.TEMPORAL:
                await self._check_temporal_correlation(rule)
            elif rule.correlation_type == CorrelationType.SPATIAL:
                await self._check_spatial_correlation(rule)
            elif rule.correlation_type == CorrelationType.ATTRIBUTE:
                await self._check_attribute_correlation(rule)
            elif rule.correlation_type == CorrelationType.BEHAVIORAL:
                await self._check_behavioral_correlation(rule)
            elif rule.correlation_type == CorrelationType.STATISTICAL:
                await self._check_statistical_correlation(rule)
            elif rule.correlation_type == CorrelationType.ML_BASED:
                await self._check_ml_correlation(rule)
            
        except Exception as e:
            self.logger.error(f"Failed to check correlation rule {rule.name}: {e}")
    
    async def _check_temporal_correlation(self, rule: CorrelationRule):
        """Проверяет временную корреляцию"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=rule.time_window)
            
            # Проверяем все группы событий
            for event_key, events in self.event_cache.items():
                # Фильтруем события по времени
                recent_events = [
                    e for e in events
                    if e['timestamp'] >= cutoff_time
                ]
                
                # Проверяем количество событий
                if rule.min_events <= len(recent_events) <= rule.max_events:
                    # Вычисляем временную корреляцию
                    correlation_result = await self._analyze_temporal_correlation(rule, recent_events)
                    
                    if correlation_result and correlation_result.confidence >= rule.confidence_threshold:
                        await self._process_correlation_result(correlation_result)
                        
        except Exception as e:
            self.logger.error(f"Failed to check temporal correlation: {e}")
    
    async def _check_spatial_correlation(self, rule: CorrelationRule):
        """Проверяет пространственную корреляцию"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=rule.time_window)
            
            # Группируем события по географическому расположению
            location_groups = defaultdict(list)
            
            for event_key, events in self.event_cache.items():
                recent_events = [
                    e for e in events
                    if e['timestamp'] >= cutoff_time
                ]
                
                for event_data in recent_events:
                    event = event_data['event']
                    location = self._extract_location(event)
                    if location:
                        location_groups[location].append(event_data)
            
            # Проверяем пространственную корреляцию для каждой группы
            for location, events in location_groups.items():
                if rule.min_events <= len(events) <= rule.max_events:
                    correlation_result = await self._analyze_spatial_correlation(rule, events, location)
                    
                    if correlation_result and correlation_result.confidence >= rule.confidence_threshold:
                        await self._process_correlation_result(correlation_result)
                        
        except Exception as e:
            self.logger.error(f"Failed to check spatial correlation: {e}")
    
    async def _check_attribute_correlation(self, rule: CorrelationRule):
        """Проверяет корреляцию по атрибутам"""
        try:
            cutoff_time = datetime.now(timezone.utc) - timedelta(seconds=rule.time_window)
            
            # Группируем события по атрибутам
            attribute_groups = defaultdict(list)
            
            for event_key, events in self.event_cache.items():
                recent_events = [
                    e for e in events
                    if e['timestamp'] >= cutoff_time
                ]
                
                for event_data in recent_events:
                    event = event_data['event']
                    attribute_key = self._create_attribute_key(event, rule.correlation_fields)
                    if attribute_key:
                        attribute_groups[attribute_key].append(event_data)
            
            # Проверяем корреляцию по атрибутам для каждой группы
            for attribute_key, events in attribute_groups.items():
                if rule.min_events <= len(events) <= rule.max_events:
                    correlation_result = await self._analyze_attribute_correlation(rule, events, attribute_key)
                    
                    if correlation_result and correlation_result.confidence >= rule.confidence_threshold:
                        await self._process_correlation_result(correlation_result)
                        
        except Exception as e:
            self.logger.error(f"Failed to check attribute correlation: {e}")
    
    async def _check_behavioral_correlation(self, rule: CorrelationRule):
        """Проверяет поведенческую корреляцию"""
        try:
            # TODO: Реализовать поведенческую корреляцию
            # Это может включать анализ паттернов поведения пользователей,
            # аномалий в последовательности событий и т.д.
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to check behavioral correlation: {e}")
    
    async def _check_statistical_correlation(self, rule: CorrelationRule):
        """Проверяет статистическую корреляцию"""
        try:
            # TODO: Реализовать статистическую корреляцию
            # Это может включать анализ распределений, трендов,
            # аномалий в статистических показателях и т.д.
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to check statistical correlation: {e}")
    
    async def _check_ml_correlation(self, rule: CorrelationRule):
        """Проверяет корреляцию на основе машинного обучения"""
        try:
            # TODO: Реализовать ML-корреляцию
            # Это может включать использование предобученных моделей
            # для выявления сложных паттернов и аномалий
            pass
            
        except Exception as e:
            self.logger.error(f"Failed to check ML correlation: {e}")
    
    async def _analyze_temporal_correlation(self, rule: CorrelationRule, events: List[Dict]) -> Optional[CorrelationResult]:
        """Анализирует временную корреляцию"""
        try:
            if len(events) < rule.min_events:
                return None
            
            # Сортируем события по времени
            sorted_events = sorted(events, key=lambda x: x['timestamp'])
            
            # Вычисляем временные интервалы
            time_intervals = []
            for i in range(1, len(sorted_events)):
                interval = (sorted_events[i]['timestamp'] - sorted_events[i-1]['timestamp']).total_seconds()
                time_intervals.append(interval)
            
            # Анализируем паттерны
            patterns = self._analyze_temporal_patterns(time_intervals)
            
            # Вычисляем уверенность
            confidence = self._calculate_temporal_confidence(time_intervals, patterns)
            
            # Определяем силу корреляции
            strength = self._determine_correlation_strength(confidence)
            
            # Создаем результат
            correlation_result = CorrelationResult(
                rule_name=rule.name,
                correlation_type=rule.correlation_type,
                strength=strength,
                confidence=confidence,
                events=[e['event'] for e in events],
                event_count=len(events),
                correlation_id=f"temp_{rule.name}_{hash(tuple(e['event'].get('id', '') for e in events))}",
                created_at=datetime.now(timezone.utc),
                time_span=(sorted_events[-1]['timestamp'] - sorted_events[0]['timestamp']).total_seconds(),
                patterns=patterns
            )
            
            return correlation_result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze temporal correlation: {e}")
            return None
    
    async def _analyze_spatial_correlation(self, rule: CorrelationRule, events: List[Dict], location: str) -> Optional[CorrelationResult]:
        """Анализирует пространственную корреляцию"""
        try:
            if len(events) < rule.min_events:
                return None
            
            # Вычисляем пространственные расстояния
            distances = self._calculate_spatial_distances(events)
            
            # Анализируем пространственные паттерны
            patterns = self._analyze_spatial_patterns(distances)
            
            # Вычисляем уверенность
            confidence = self._calculate_spatial_confidence(distances, patterns)
            
            # Определяем силу корреляции
            strength = self._determine_correlation_strength(confidence)
            
            # Создаем результат
            correlation_result = CorrelationResult(
                rule_name=rule.name,
                correlation_type=rule.correlation_type,
                strength=strength,
                confidence=confidence,
                events=[e['event'] for e in events],
                event_count=len(events),
                correlation_id=f"spatial_{rule.name}_{hash(location)}",
                created_at=datetime.now(timezone.utc),
                time_span=0,  # Для пространственной корреляции время не важно
                spatial_distance=sum(distances) / len(distances) if distances else 0,
                patterns=patterns
            )
            
            return correlation_result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze spatial correlation: {e}")
            return None
    
    async def _analyze_attribute_correlation(self, rule: CorrelationRule, events: List[Dict], attribute_key: str) -> Optional[CorrelationResult]:
        """Анализирует корреляцию по атрибутам"""
        try:
            if len(events) < rule.min_events:
                return None
            
            # Анализируем атрибуты событий
            attribute_analysis = self._analyze_event_attributes(events, rule.correlation_fields)
            
            # Вычисляем уверенность
            confidence = self._calculate_attribute_confidence(attribute_analysis)
            
            # Определяем силу корреляции
            strength = self._determine_correlation_strength(confidence)
            
            # Создаем результат
            correlation_result = CorrelationResult(
                rule_name=rule.name,
                correlation_type=rule.correlation_type,
                strength=strength,
                confidence=confidence,
                events=[e['event'] for e in events],
                event_count=len(events),
                correlation_id=f"attr_{rule.name}_{hash(attribute_key)}",
                created_at=datetime.now(timezone.utc),
                time_span=0,
                attributes=attribute_analysis,
                patterns=self._extract_attribute_patterns(attribute_analysis)
            )
            
            return correlation_result
            
        except Exception as e:
            self.logger.error(f"Failed to analyze attribute correlation: {e}")
            return None
    
    def _analyze_temporal_patterns(self, time_intervals: List[float]) -> List[str]:
        """Анализирует временные паттерны"""
        patterns = []
        
        if not time_intervals:
            return patterns
        
        # Анализ регулярности
        mean_interval = sum(time_intervals) / len(time_intervals)
        variance = sum((x - mean_interval) ** 2 for x in time_intervals) / len(time_intervals)
        
        if variance < mean_interval * 0.1:
            patterns.append("regular_timing")
        elif variance > mean_interval * 2:
            patterns.append("irregular_timing")
        else:
            patterns.append("moderate_timing")
        
        # Анализ трендов
        if len(time_intervals) > 2:
            trend = self._calculate_trend(time_intervals)
            if trend > 0.1:
                patterns.append("increasing_frequency")
            elif trend < -0.1:
                patterns.append("decreasing_frequency")
            else:
                patterns.append("stable_frequency")
        
        return patterns
    
    def _analyze_spatial_patterns(self, distances: List[float]) -> List[str]:
        """Анализирует пространственные паттерны"""
        patterns = []
        
        if not distances:
            return patterns
        
        # Анализ кластеризации
        mean_distance = sum(distances) / len(distances)
        small_distances = [d for d in distances if d < mean_distance * 0.5]
        
        if len(small_distances) > len(distances) * 0.7:
            patterns.append("clustered")
        elif len(small_distances) < len(distances) * 0.3:
            patterns.append("dispersed")
        else:
            patterns.append("mixed_distribution")
        
        return patterns
    
    def _analyze_event_attributes(self, events: List[Dict], fields: List[str]) -> Dict[str, Any]:
        """Анализирует атрибуты событий"""
        analysis = {}
        
        for field in fields:
            values = []
            for event_data in events:
                event = event_data['event']
                value = self._get_field_value(event, field)
                if value is not None:
                    values.append(value)
            
            if values:
                analysis[field] = {
                    'unique_count': len(set(values)),
                    'total_count': len(values),
                    'most_common': self._get_most_common(values),
                    'diversity': len(set(values)) / len(values) if values else 0
                }
        
        return analysis
    
    def _extract_attribute_patterns(self, attribute_analysis: Dict[str, Any]) -> List[str]:
        """Извлекает паттерны из анализа атрибутов"""
        patterns = []
        
        for field, analysis in attribute_analysis.items():
            if analysis['diversity'] < 0.2:
                patterns.append(f"low_diversity_{field}")
            elif analysis['diversity'] > 0.8:
                patterns.append(f"high_diversity_{field}")
            
            if analysis['unique_count'] == 1:
                patterns.append(f"single_value_{field}")
        
        return patterns
    
    def _calculate_temporal_confidence(self, time_intervals: List[float], patterns: List[str]) -> float:
        """Вычисляет уверенность временной корреляции"""
        if not time_intervals:
            return 0.0
        
        # Базовая уверенность
        confidence = 0.5
        
        # Увеличиваем уверенность на основе паттернов
        if "regular_timing" in patterns:
            confidence += 0.2
        if "stable_frequency" in patterns:
            confidence += 0.15
        
        # Увеличиваем уверенность на основе количества событий
        if len(time_intervals) > 10:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_spatial_confidence(self, distances: List[float], patterns: List[str]) -> float:
        """Вычисляет уверенность пространственной корреляции"""
        if not distances:
            return 0.0
        
        # Базовая уверенность
        confidence = 0.5
        
        # Увеличиваем уверенность на основе паттернов
        if "clustered" in patterns:
            confidence += 0.3
        elif "mixed_distribution" in patterns:
            confidence += 0.15
        
        # Увеличиваем уверенность на основе количества событий
        if len(distances) > 5:
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _calculate_attribute_confidence(self, attribute_analysis: Dict[str, Any]) -> float:
        """Вычисляет уверенность корреляции по атрибутам"""
        if not attribute_analysis:
            return 0.0
        
        # Базовая уверенность
        confidence = 0.5
        
        # Анализируем каждый атрибут
        for field, analysis in attribute_analysis.items():
            if analysis['diversity'] < 0.3:
                confidence += 0.1  # Низкое разнообразие указывает на корреляцию
            elif analysis['diversity'] > 0.8:
                confidence -= 0.05  # Высокое разнообразие снижает корреляцию
        
        return max(0.0, min(confidence, 1.0))
    
    def _determine_correlation_strength(self, confidence: float) -> CorrelationStrength:
        """Определяет силу корреляции на основе уверенности"""
        if confidence >= 0.9:
            return CorrelationStrength.VERY_STRONG
        elif confidence >= 0.8:
            return CorrelationStrength.STRONG
        elif confidence >= 0.6:
            return CorrelationStrength.MODERATE
        else:
            return CorrelationStrength.WEAK
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Вычисляет тренд в последовательности значений"""
        if len(values) < 2:
            return 0.0
        
        # Простой линейный тренд
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * v for i, v in enumerate(values))
        x2_sum = sum(i * i for i in range(n))
        
        try:
            slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum)
            return slope
        except ZeroDivisionError:
            return 0.0
    
    def _calculate_spatial_distances(self, events: List[Dict]) -> List[float]:
        """Вычисляет пространственные расстояния между событиями"""
        distances = []
        
        # TODO: Реализовать реальный расчет пространственных расстояний
        # Пока возвращаем фиктивные значения
        for i in range(len(events) - 1):
            distances.append(0.1)  # Фиктивное расстояние
        
        return distances
    
    def _extract_location(self, event: Dict[str, Any]) -> Optional[str]:
        """Извлекает информацию о местоположении из события"""
        # TODO: Реализовать извлечение координат или геолокации
        # Пока возвращаем None
        return None
    
    def _create_attribute_key(self, event: Dict[str, Any], fields: List[str]) -> Optional[str]:
        """Создает ключ атрибута для группировки"""
        if not fields:
            return None
        
        key_parts = []
        for field in fields:
            value = self._get_field_value(event, field)
            if value is not None:
                key_parts.append(f"{field}={value}")
        
        return ":".join(key_parts) if key_parts else None
    
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
    
    def _get_most_common(self, values: List[Any]) -> Any:
        """Получает наиболее часто встречающееся значение"""
        if not values:
            return None
        
        from collections import Counter
        counter = Counter(values)
        return counter.most_common(1)[0][0]
    
    async def _process_correlation_result(self, result: CorrelationResult):
        """Обрабатывает результат корреляции"""
        try:
            # Сохраняем результат
            self.correlation_cache[result.rule_name].append(result)
            
            # Обновляем статистику
            self.stats['correlations_found'] += 1
            
            # Логируем результат
            self.logger.info(
                f"Correlation found: {result.rule_name} - "
                f"Strength: {result.strength.value}, "
                f"Confidence: {result.confidence:.2f}, "
                f"Events: {result.event_count}"
            )
            
            # TODO: Отправить уведомление или создать алерт
            
        except Exception as e:
            self.logger.error(f"Failed to process correlation result: {e}")
    
    def get_correlation_results(self, rule_name: Optional[str] = None) -> List[CorrelationResult]:
        """Получает результаты корреляции"""
        if rule_name:
            return self.correlation_cache.get(rule_name, [])
        else:
            all_results = []
            for results in self.correlation_cache.values():
                all_results.extend(results)
            return all_results
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику движка корреляции"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'rules_loaded': len(self.correlation_rules),
            'active_rules': len([r for r in self.correlation_rules if r.enabled]),
            'event_cache_size': sum(len(events) for events in self.event_cache.values()),
            'correlation_cache_size': sum(len(results) for results in self.correlation_cache.values()),
            'pattern_cache_size': len(self.pattern_cache)
        }
    
    def add_correlation_rule(self, rule: CorrelationRule):
        """Добавляет новое правило корреляции"""
        self.correlation_rules.append(rule)
        self.logger.info(f"Added correlation rule: {rule.name}")
    
    def remove_correlation_rule(self, rule_name: str):
        """Удаляет правило корреляции"""
        self.correlation_rules = [r for r in self.correlation_rules if r.name != rule_name]
        self.logger.info(f"Removed correlation rule: {rule_name}")
    
    def reload_rules(self):
        """Перезагружает правила корреляции"""
        self.logger.info("Reloading correlation rules...")
        self._load_correlation_rules()


# Глобальный экземпляр движка корреляции
correlation_engine = CorrelationEngine()
