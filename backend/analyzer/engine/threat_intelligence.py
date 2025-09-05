"""
Threat Intelligence Service - Сервис угроз и разведки для SIEM системы

Функциональность:
- Анализ угроз на основе событий
- Интеграция с внешними источниками угроз
- Классификация угроз
- Оценка рисков
- Блокировка угроз
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Tuple
import asyncio
import json
import logging
import hashlib
import ipaddress
from pathlib import Path
from collections import defaultdict, deque

try:
    import yaml
except ImportError:
    yaml = None

try:
    import aiohttp
except ImportError:
    aiohttp = None


class ThreatType(str, Enum):
    """Типы угроз"""
    MALWARE = "malware"                    # Вредоносное ПО
    PHISHING = "phishing"                  # Фишинг
    DDoS = "ddos"                          # DDoS атаки
    BRUTE_FORCE = "brute_force"            # Брутфорс атаки
    SQL_INJECTION = "sql_injection"        # SQL инъекции
    XSS = "xss"                            # XSS атаки
    PORT_SCAN = "port_scan"                # Сканирование портов
    EXPLOIT = "exploit"                    # Эксплойты
    DATA_EXFILTRATION = "data_exfiltration" # Утечка данных
    INSIDER_THREAT = "insider_threat"      # Внутренние угрозы
    APT = "apt"                            # Продвинутые постоянные угрозы
    RANSOMWARE = "ransomware"              # Рансваре
    UNKNOWN = "unknown"                    # Неизвестная угроза


class ThreatSeverity(str, Enum):
    """Уровни важности угроз"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatStatus(str, Enum):
    """Статусы угроз"""
    NEW = "new"                    # Новая угроза
    ANALYZING = "analyzing"        # Анализируется
    CONFIRMED = "confirmed"        # Подтверждена
    FALSE_POSITIVE = "false_positive"  # Ложное срабатывание
    MITIGATED = "mitigated"        # Смягчена
    RESOLVED = "resolved"          # Решена


class ThreatSource(str, Enum):
    """Источники угроз"""
    INTERNAL = "internal"          # Внутренний источник
    EXTERNAL = "external"          # Внешний источник
    UNKNOWN = "unknown"            # Неизвестный источник


@dataclass
class ThreatIndicator:
    """Индикатор угрозы"""
    # Основные параметры
    id: str
    type: ThreatType
    value: str  # IP, URL, хеш файла, домен и т.д.
    severity: ThreatSeverity
    status: ThreatStatus = ThreatStatus.NEW
    
    # Метаданные
    source: ThreatSource = ThreatSource.UNKNOWN
    confidence: float = 0.8  # 0.0 - 1.0
    description: str = ""
    tags: List[str] = field(default_factory=list)
    
    # Временные метки
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Дополнительные данные
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_indicators: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует индикатор угрозы в словарь"""
        return {
            'id': self.id,
            'type': self.type.value,
            'value': self.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'source': self.source.value,
            'confidence': self.confidence,
            'description': self.description,
            'tags': self.tags,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'related_indicators': self.related_indicators
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThreatIndicator':
        """Создает индикатор угрозы из словаря"""
        # Преобразуем enum значения
        data['type'] = ThreatType(data['type'])
        data['severity'] = ThreatSeverity(data['severity'])
        data['status'] = ThreatStatus(data['status'])
        data['source'] = ThreatSource(data['source'])
        
        # Преобразуем даты
        date_fields = ['first_seen', 'last_seen', 'created_at', 'updated_at']
        for field_name in date_fields:
            if field_name in data and data[field_name]:
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)
    
    def update_last_seen(self):
        """Обновляет время последнего появления"""
        self.last_seen = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def is_expired(self, max_age_days: int = 90) -> bool:
        """Проверяет, истек ли срок действия индикатора"""
        cutoff_time = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        return self.last_seen < cutoff_time
    
    def get_age_days(self) -> int:
        """Возвращает возраст индикатора в днях"""
        return (datetime.now(timezone.utc) - self.first_seen).days


@dataclass
class ThreatReport:
    """Отчет об угрозе"""
    # Основные параметры
    id: str
    title: str
    description: str
    threat_type: ThreatType
    severity: ThreatSeverity
    status: ThreatStatus = ThreatStatus.NEW
    
    # Индикаторы
    indicators: List[ThreatIndicator] = field(default_factory=list)
    
    # Метаданные
    source: str = "threat_intelligence"
    confidence: float = 0.8
    tags: List[str] = field(default_factory=list)
    category: str = "general"
    
    # Временные метки
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Дополнительные данные
    metadata: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if self.updated_at is None:
            self.updated_at = self.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразует отчет об угрозе в словарь"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'threat_type': self.threat_type.value,
            'severity': self.severity.value,
            'status': self.status.value,
            'indicators': [indicator.to_dict() for indicator in self.indicators],
            'source': self.source,
            'confidence': self.confidence,
            'tags': self.tags,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'metadata': self.metadata,
            'recommendations': self.recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThreatReport':
        """Создает отчет об угрозе из словаря"""
        # Преобразуем enum значения
        data['threat_type'] = ThreatType(data['threat_type'])
        data['severity'] = ThreatSeverity(data['severity'])
        data['status'] = ThreatStatus(data['status'])
        
        # Преобразуем индикаторы
        if 'indicators' in data:
            data['indicators'] = [
                ThreatIndicator.from_dict(indicator_data) 
                for indicator_data in data['indicators']
            ]
        
        # Преобразуем даты
        date_fields = ['created_at', 'updated_at']
        for field_name in date_fields:
            if field_name in data and data[field_name]:
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)


class ThreatIntelligenceService:
    """Сервис угроз и разведки"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger("threat_intelligence")
        self.config = self._load_config_from_object(config) if config else self._load_config()
        
        # Хранилище данных
        self.indicators: Dict[str, ThreatIndicator] = {}
        self.threat_reports: Dict[str, ThreatReport] = {}
        self.ioc_cache: Dict[str, List[ThreatIndicator]] = defaultdict(list)
        
        # Внешние источники
        self.external_sources: Dict[str, Dict[str, Any]] = {}
        
        # Кэши и индексы
        self.ip_indicators: Dict[str, List[ThreatIndicator]] = defaultdict(list)
        self.domain_indicators: Dict[str, List[ThreatIndicator]] = defaultdict(list)
        self.url_indicators: Dict[str, List[ThreatIndicator]] = defaultdict(list)
        self.hash_indicators: Dict[str, List[ThreatIndicator]] = defaultdict(list)
        
        # Статистика
        self.stats = {
            'indicators_total': 0,
            'indicators_active': 0,
            'threat_reports_total': 0,
            'threats_detected': 0,
            'false_positives': 0,
            'external_sources_checked': 0
        }
        
        # Состояние
        self.is_running = False
        
        # Загружаем конфигурацию и данные
        self._load_external_sources()
        self._load_indicators()
        self._build_indexes()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Загружает конфигурацию сервиса угроз"""
        default_config = {
            'enable_external_sources': True,
            'enable_auto_blocking': False,
            'enable_risk_scoring': True,
            'max_indicators_per_source': 10000,
            'update_interval': 3600,  # 1 час
            'confidence_threshold': 0.7,
            'max_age_days': 90,
            'enable_ml_detection': False,
            'enable_behavioral_analysis': True,
            'enable_reputation_checking': True
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
    
    def _load_external_sources(self):
        """Загружает конфигурацию внешних источников угроз"""
        sources_file = Path(__file__).parent.parent / "threat_sources.yaml"
        
        if sources_file.exists() and yaml:
            try:
                with open(sources_file, 'r', encoding='utf-8') as f:
                    sources_data = yaml.safe_load(f) or {}
                    self.external_sources = sources_data.get('sources', {})
                    
                self.logger.info(f"Loaded {len(self.external_sources)} external threat sources")
                
            except Exception as e:
                self.logger.error(f"Failed to load external sources: {e}")
        
        # Встроенные источники
        builtin_sources = {
            'abuseipdb': {
                'enabled': True,
                'type': 'api',
                'url': 'https://api.abuseipdb.com/api/v2/check',
                'api_key_required': True,
                'rate_limit': 1000,
                'update_interval': 3600
            },
            'virustotal': {
                'enabled': True,
                'type': 'api',
                'url': 'https://www.virustotal.com/vtapi/v2',
                'api_key_required': True,
                'rate_limit': 500,
                'update_interval': 3600
            },
            'alienvault_otx': {
                'enabled': True,
                'type': 'api',
                'url': 'https://otx.alienvault.com/api/v1',
                'api_key_required': True,
                'rate_limit': 1000,
                'update_interval': 3600
            }
        }
        
        # Обновляем встроенными источниками
        for name, source in builtin_sources.items():
            if name not in self.external_sources:
                self.external_sources[name] = source
    
    def _load_indicators(self):
        """Загружает индикаторы угроз"""
        indicators_file = Path(__file__).parent.parent / "indicators.yaml"
        
        if indicators_file.exists() and yaml:
            try:
                with open(indicators_file, 'r', encoding='utf-8') as f:
                    indicators_data = yaml.safe_load(f) or {}
                    
                    # Загружаем индикаторы
                    for indicator_data in indicators_data.get('indicators', []):
                        try:
                            indicator = ThreatIndicator.from_dict(indicator_data)
                            self.indicators[indicator.id] = indicator
                        except Exception as e:
                            self.logger.error(f"Failed to load indicator: {e}")
                    
                    # Загружаем отчеты об угрозах
                    for report_data in indicators_data.get('threat_reports', []):
                        try:
                            report = ThreatReport.from_dict(report_data)
                            self.threat_reports[report.id] = report
                        except Exception as e:
                            self.logger.error(f"Failed to load threat report: {e}")
                    
                self.logger.info(f"Loaded {len(self.indicators)} indicators and {len(self.threat_reports)} threat reports")
                
            except Exception as e:
                self.logger.error(f"Failed to load indicators: {e}")
    
    def _build_indexes(self):
        """Строит индексы для быстрого поиска"""
        for indicator in self.indicators.values():
            self._add_to_indexes(indicator)
        
        self.stats['indicators_total'] = len(self.indicators)
        self.stats['indicators_active'] = len([i for i in self.indicators.values() if i.status == ThreatStatus.CONFIRMED])
    
    def _add_to_indexes(self, indicator: ThreatIndicator):
        """Добавляет индикатор в индексы"""
        try:
            # Определяем тип индикатора и добавляем в соответствующий индекс
            if self._is_ip_address(indicator.value):
                self.ip_indicators[indicator.value].append(indicator)
            elif self._is_domain(indicator.value):
                self.domain_indicators[indicator.value].append(indicator)
            elif self._is_url(indicator.value):
                self.url_indicators[indicator.value].append(indicator)
            elif self._is_hash(indicator.value):
                self.hash_indicators[indicator.value].append(indicator)
            
            # Добавляем в общий кэш IOC
            self.ioc_cache[indicator.type.value].append(indicator)
            
        except Exception as e:
            self.logger.error(f"Failed to add indicator to indexes: {e}")
    
    def _is_ip_address(self, value: str) -> bool:
        """Проверяет, является ли значение IP адресом"""
        try:
            ipaddress.ip_address(value)
            return True
        except ValueError:
            return False
    
    def _is_domain(self, value: str) -> bool:
        """Проверяет, является ли значение доменом"""
        # Простая проверка - можно улучшить
        return '.' in value and not value.startswith('http') and not value.startswith('ftp')
    
    def _is_url(self, value: str) -> bool:
        """Проверяет, является ли значение URL"""
        return value.startswith(('http://', 'https://', 'ftp://'))
    
    def _is_hash(self, value: str) -> bool:
        """Проверяет, является ли значение хешем"""
        # Проверяем MD5, SHA1, SHA256
        hash_lengths = [32, 40, 64]
        return len(value) in hash_lengths and all(c in '0123456789abcdefABCDEF' for c in value)
    
    async def start(self):
        """Запускает сервис угроз и разведки"""
        if self.is_running:
            return
        
        self.is_running = True
        self.logger.info("Threat intelligence service started")
        
        # Запускаем обновление внешних источников
        if self.config['enable_external_sources']:
            asyncio.create_task(self._external_sources_updater())
    
    async def stop(self):
        """Останавливает сервис угроз и разведки"""
        self.is_running = False
        self.logger.info("Threat intelligence service stopped")
    
    async def check_threat(self, event: Dict[str, Any]) -> Optional[ThreatReport]:
        """Проверяет событие на наличие угроз"""
        try:
            # Извлекаем потенциальные индикаторы из события
            indicators = self._extract_indicators_from_event(event)
            
            if not indicators:
                return None
            
            # Проверяем каждый индикатор
            matched_indicators = []
            
            for indicator_value, indicator_type in indicators:
                matched = await self._check_indicator(indicator_value, indicator_type)
                if matched:
                    matched_indicators.extend(matched)
            
            if not matched_indicators:
                return None
            
            # Создаем отчет об угрозе
            threat_report = await self._create_threat_report(event, matched_indicators)
            
            # Обновляем статистику
            self.stats['threats_detected'] += 1
            
            return threat_report
            
        except Exception as e:
            self.logger.error(f"Failed to check threat: {e}")
            return None
    
    def _extract_indicators_from_event(self, event: Dict[str, Any]) -> List[Tuple[str, ThreatType]]:
        """Извлекает потенциальные индикаторы из события"""
        indicators = []
        
        # IP адреса
        for ip_field in ['src_ip', 'dst_ip']:
            if ip_field in event and event[ip_field]:
                indicators.append((event[ip_field], ThreatType.UNKNOWN))
        
        # Домены
        if 'details' in event and isinstance(event['details'], dict):
            details = event['details']
            
            # Проверяем различные поля на наличие доменов
            for field in ['domain', 'hostname', 'server']:
                if field in details and details[field]:
                    indicators.append((details[field], ThreatType.UNKNOWN))
            
            # Проверяем URL
            if 'url' in details and details['url']:
                indicators.append((details['url'], ThreatType.UNKNOWN))
        
        # Хеши файлов
        if 'details' in event and isinstance(event['details'], dict):
            details = event['details']
            
            for field in ['file_hash', 'hash', 'md5', 'sha1', 'sha256']:
                if field in details and details[field]:
                    indicators.append((details[field], ThreatType.MALWARE))
        
        return indicators
    
    async def _check_indicator(self, value: str, indicator_type: ThreatType) -> List[ThreatIndicator]:
        """Проверяет индикатор на наличие угроз"""
        matched_indicators = []
        
        try:
            # Проверяем локальные индикаторы
            local_matches = self._check_local_indicators(value, indicator_type)
            matched_indicators.extend(local_matches)
            
            # Проверяем внешние источники
            if self.config['enable_external_sources']:
                external_matches = await self._check_external_sources(value, indicator_type)
                matched_indicators.extend(external_matches)
            
            # Обновляем время последнего появления для найденных индикаторов
            for indicator in matched_indicators:
                indicator.update_last_seen()
            
        except Exception as e:
            self.logger.error(f"Failed to check indicator {value}: {e}")
        
        return matched_indicators
    
    def _check_local_indicators(self, value: str, indicator_type: ThreatType) -> List[ThreatIndicator]:
        """Проверяет локальные индикаторы угроз"""
        matched_indicators = []
        
        try:
            # Проверяем IP адреса
            if self._is_ip_address(value):
                if value in self.ip_indicators:
                    matched_indicators.extend(self.ip_indicators[value])
            
            # Проверяем домены
            elif self._is_domain(value):
                if value in self.domain_indicators:
                    matched_indicators.extend(self.domain_indicators[value])
            
            # Проверяем URL
            elif self._is_url(value):
                if value in self.url_indicators:
                    matched_indicators.extend(self.url_indicators[value])
            
            # Проверяем хеши
            elif self._is_hash(value):
                if value in self.hash_indicators:
                    matched_indicators.extend(self.hash_indicators[value])
            
            # Фильтруем по типу угрозы
            if indicator_type != ThreatType.UNKNOWN:
                matched_indicators = [
                    i for i in matched_indicators 
                    if i.type == indicator_type
                ]
            
            # Фильтруем по статусу и уверенности
            matched_indicators = [
                i for i in matched_indicators
                if i.status == ThreatStatus.CONFIRMED and 
                i.confidence >= self.config['confidence_threshold']
            ]
            
        except Exception as e:
            self.logger.error(f"Failed to check local indicators: {e}")
        
        return matched_indicators
    
    async def _check_external_sources(self, value: str, indicator_type: ThreatType) -> List[ThreatIndicator]:
        """Проверяет внешние источники угроз"""
        matched_indicators = []
        
        try:
            for source_name, source_config in self.external_sources.items():
                if not source_config.get('enabled', False):
                    continue
                
                try:
                    # Проверяем ограничения скорости
                    if not self._check_rate_limit(source_name, source_config):
                        continue
                    
                    # Выполняем проверку
                    result = await self._query_external_source(source_name, source_config, value, indicator_type)
                    
                    if result:
                        # Создаем индикатор угрозы
                        indicator = ThreatIndicator(
                            id=f"{source_name}_{hash(value)}",
                            type=indicator_type,
                            value=value,
                            severity=result.get('severity', ThreatSeverity.MEDIUM),
                            source=ThreatSource.EXTERNAL,
                            confidence=result.get('confidence', 0.8),
                            description=result.get('description', f"Threat detected by {source_name}"),
                            tags=[source_name] + result.get('tags', []),
                            metadata={'source': source_name, 'raw_result': result}
                        )
                        
                        matched_indicators.append(indicator)
                        
                        # Сохраняем индикатор
                        self.indicators[indicator.id] = indicator
                        self._add_to_indexes(indicator)
                        
                        # Обновляем статистику
                        self.stats['external_sources_checked'] += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to check external source {source_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to check external sources: {e}")
        
        return matched_indicators
    
    def _check_rate_limit(self, source_name: str, source_config: Dict[str, Any]) -> bool:
        """Проверяет ограничения скорости для внешнего источника"""
        # TODO: Реализовать проверку ограничений скорости
        return True
    
    async def _query_external_source(self, source_name: str, source_config: Dict[str, Any], value: str, indicator_type: ThreatType) -> Optional[Dict[str, Any]]:
        """Выполняет запрос к внешнему источнику угроз"""
        try:
            if source_config.get('type') == 'api':
                return await self._query_api_source(source_name, source_config, value, indicator_type)
            else:
                self.logger.warning(f"Unknown source type for {source_name}: {source_config.get('type')}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to query external source {source_name}: {e}")
            return None
    
    async def _query_api_source(self, source_name: str, source_config: Dict[str, Any], value: str, indicator_type: ThreatType) -> Optional[Dict[str, Any]]:
        """Выполняет запрос к API источнику угроз"""
        if not aiohttp:
            self.logger.warning("aiohttp not available for API queries")
            return None
        
        try:
            # TODO: Реализовать реальные API запросы
            # Пока возвращаем фиктивный результат для демонстрации
            
            if source_name == 'abuseipdb' and self._is_ip_address(value):
                return {
                    'severity': ThreatSeverity.MEDIUM,
                    'confidence': 0.8,
                    'description': f"IP {value} reported for abuse",
                    'tags': ['abuse', 'reported']
                }
            
            elif source_name == 'virustotal' and self._is_hash(value):
                return {
                    'severity': ThreatSeverity.HIGH,
                    'confidence': 0.9,
                    'description': f"Hash {value} detected as malicious",
                    'tags': ['malware', 'detected']
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to query API source {source_name}: {e}")
            return None
    
    async def _create_threat_report(self, event: Dict[str, Any], indicators: List[ThreatIndicator]) -> ThreatReport:
        """Создает отчет об угрозе на основе события и индикаторов"""
        try:
            # Определяем тип угрозы
            threat_type = self._determine_threat_type(indicators, event)
            
            # Определяем важность угрозы
            severity = self._determine_threat_severity(indicators, event)
            
            # Создаем отчет
            report = ThreatReport(
                id=f"threat_{hash(str(event.get('id', '')) + str(indicators[0].id))}",
                title=f"Threat detected: {threat_type.value}",
                description=f"Threat detected based on {len(indicators)} indicators",
                threat_type=threat_type,
                severity=severity,
                indicators=indicators,
                source="threat_intelligence",
                confidence=sum(i.confidence for i in indicators) / len(indicators),
                tags=[i.type.value for i in indicators],
                category="automated_detection",
                recommendations=self._generate_recommendations(threat_type, severity)
            )
            
            # Сохраняем отчет
            self.threat_reports[report.id] = report
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to create threat report: {e}")
            raise
    
    def _determine_threat_type(self, indicators: List[ThreatIndicator], event: Dict[str, Any]) -> ThreatType:
        """Определяет тип угрозы на основе индикаторов и события"""
        # Приоритет по типам индикаторов
        type_priorities = {
            ThreatType.MALWARE: 10,
            ThreatType.RANSOMWARE: 9,
            ThreatType.APT: 8,
            ThreatType.EXPLOIT: 7,
            ThreatType.DDoS: 6,
            ThreatType.BRUTE_FORCE: 5,
            ThreatType.PORT_SCAN: 4,
            ThreatType.PHISHING: 3,
            ThreatType.SQL_INJECTION: 2,
            ThreatType.XSS: 1,
            ThreatType.UNKNOWN: 0
        }
        
        # Находим индикатор с наивысшим приоритетом
        best_indicator = max(indicators, key=lambda i: type_priorities.get(i.type, 0))
        
        # Дополнительная логика на основе события
        event_type = event.get('event_type', '')
        
        if 'portscan' in event_type.lower():
            return ThreatType.PORT_SCAN
        elif 'brute' in event_type.lower() or 'auth' in event_type.lower():
            return ThreatType.BRUTE_FORCE
        elif 'ddos' in event_type.lower():
            return ThreatType.DDoS
        elif 'sql' in event_type.lower():
            return ThreatType.SQL_INJECTION
        elif 'xss' in event_type.lower():
            return ThreatType.XSS
        
        return best_indicator.type
    
    def _determine_threat_severity(self, indicators: List[ThreatIndicator], event: Dict[str, Any]) -> ThreatSeverity:
        """Определяет важность угрозы"""
        # Базовая важность на основе индикаторов
        base_severity = max(indicators, key=lambda i: self._severity_to_numeric(i.severity)).severity
        
        # Повышаем важность на основе количества индикаторов
        if len(indicators) >= 3:
            if base_severity == ThreatSeverity.LOW:
                base_severity = ThreatSeverity.MEDIUM
            elif base_severity == ThreatSeverity.MEDIUM:
                base_severity = ThreatSeverity.HIGH
        
        # Повышаем важность на основе типа события
        event_severity = event.get('severity', 'medium')
        if event_severity in ['high', 'critical']:
            if base_severity == ThreatSeverity.MEDIUM:
                base_severity = ThreatSeverity.HIGH
            elif base_severity == ThreatSeverity.HIGH:
                base_severity = ThreatSeverity.CRITICAL
        
        return base_severity
    
    def _severity_to_numeric(self, severity: ThreatSeverity) -> int:
        """Преобразует важность угрозы в числовое значение"""
        severity_map = {
            ThreatSeverity.INFO: 0,
            ThreatSeverity.LOW: 1,
            ThreatSeverity.MEDIUM: 2,
            ThreatSeverity.HIGH: 3,
            ThreatSeverity.CRITICAL: 4
        }
        return severity_map.get(severity, 0)
    
    def _generate_recommendations(self, threat_type: ThreatType, severity: ThreatSeverity) -> List[str]:
        """Генерирует рекомендации по устранению угрозы"""
        recommendations = []
        
        # Общие рекомендации
        if severity in [ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]:
            recommendations.append("Immediate response required")
            recommendations.append("Isolate affected systems")
            recommendations.append("Contact security team")
        
        # Специфические рекомендации по типу угрозы
        if threat_type == ThreatType.MALWARE:
            recommendations.append("Run full system scan")
            recommendations.append("Update antivirus signatures")
            recommendations.append("Check for unauthorized processes")
        
        elif threat_type == ThreatType.DDoS:
            recommendations.append("Enable DDoS protection")
            recommendations.append("Monitor network traffic")
            recommendations.append("Contact ISP if necessary")
        
        elif threat_type == ThreatType.BRUTE_FORCE:
            recommendations.append("Implement account lockout")
            recommendations.append("Enable multi-factor authentication")
            recommendations.append("Review access logs")
        
        elif threat_type == ThreatType.PORT_SCAN:
            recommendations.append("Review firewall rules")
            recommendations.append("Monitor for follow-up attacks")
            recommendations.append("Implement intrusion detection")
        
        return recommendations
    
    async def _external_sources_updater(self):
        """Обновляет данные из внешних источников угроз"""
        while self.is_running:
            try:
                await asyncio.sleep(self.config['update_interval'])
                
                if not self.config['enable_external_sources']:
                    continue
                
                self.logger.info("Updating external threat sources...")
                
                # TODO: Реализовать обновление из внешних источников
                # Это может включать загрузку новых индикаторов,
                # обновление существующих и т.д.
                
            except Exception as e:
                self.logger.error(f"External sources updater error: {e}")
    
    def add_indicator(self, indicator: ThreatIndicator):
        """Добавляет новый индикатор угрозы"""
        try:
            self.indicators[indicator.id] = indicator
            self._add_to_indexes(indicator)
            
            self.stats['indicators_total'] += 1
            if indicator.status == ThreatStatus.CONFIRMED:
                self.stats['indicators_active'] += 1
            
            self.logger.info(f"Added threat indicator: {indicator.id}")
            
        except Exception as e:
            self.logger.error(f"Failed to add indicator: {e}")
    
    def remove_indicator(self, indicator_id: str):
        """Удаляет индикатор угрозы"""
        try:
            if indicator_id in self.indicators:
                indicator = self.indicators[indicator_id]
                
                # Удаляем из индексов
                self._remove_from_indexes(indicator)
                
                # Удаляем из основного хранилища
                del self.indicators[indicator_id]
                
                # Обновляем статистику
                self.stats['indicators_total'] -= 1
                if indicator.status == ThreatStatus.CONFIRMED:
                    self.stats['indicators_active'] -= 1
                
                self.logger.info(f"Removed threat indicator: {indicator_id}")
                
        except Exception as e:
            self.logger.error(f"Failed to remove indicator: {e}")
    
    def _remove_from_indexes(self, indicator: ThreatIndicator):
        """Удаляет индикатор из всех индексов"""
        try:
            # Удаляем из IP индекса
            if indicator.value in self.ip_indicators:
                self.ip_indicators[indicator.value] = [
                    i for i in self.ip_indicators[indicator.value] 
                    if i.id != indicator.id
                ]
            
            # Удаляем из доменного индекса
            if indicator.value in self.domain_indicators:
                self.domain_indicators[indicator.value] = [
                    i for i in self.domain_indicators[indicator.value] 
                    if i.id != indicator.id
                ]
            
            # Удаляем из URL индекса
            if indicator.value in self.url_indicators:
                self.url_indicators[indicator.value] = [
                    i for i in self.url_indicators[indicator.value] 
                    if i.id != indicator.id
                ]
            
            # Удаляем из хеш индекса
            if indicator.value in self.hash_indicators:
                self.hash_indicators[indicator.value] = [
                    i for i in self.hash_indicators[indicator.value] 
                    if i.id != indicator.id
                ]
            
            # Удаляем из общего кэша IOC
            if indicator.type.value in self.ioc_cache:
                self.ioc_cache[indicator.type.value] = [
                    i for i in self.ioc_cache[indicator.type.value] 
                    if i.id != indicator.id
                ]
                
        except Exception as e:
            self.logger.error(f"Failed to remove indicator from indexes: {e}")
    
    def get_indicators_by_type(self, indicator_type: ThreatType) -> List[ThreatIndicator]:
        """Получает индикаторы по типу"""
        return self.ioc_cache.get(indicator_type.value, [])
    
    def get_indicators_by_value(self, value: str) -> List[ThreatIndicator]:
        """Получает индикаторы по значению"""
        indicators = []
        
        if self._is_ip_address(value):
            indicators.extend(self.ip_indicators.get(value, []))
        elif self._is_domain(value):
            indicators.extend(self.domain_indicators.get(value, []))
        elif self._is_url(value):
            indicators.extend(self.url_indicators.get(value, []))
        elif self._is_hash(value):
            indicators.extend(self.hash_indicators.get(value, []))
        
        return indicators
    
    def get_threat_reports(self, status: Optional[ThreatStatus] = None) -> List[ThreatReport]:
        """Получает отчеты об угрозах"""
        if status is None:
            return list(self.threat_reports.values())
        
        return [
            report for report in self.threat_reports.values()
            if report.status == status
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику сервиса угроз"""
        return {
            **self.stats,
            'is_running': self.is_running,
            'external_sources_count': len(self.external_sources),
            'threat_reports_count': len(self.threat_reports),
            'ip_indicators_count': len(self.ip_indicators),
            'domain_indicators_count': len(self.domain_indicators),
            'url_indicators_count': len(self.url_indicators),
            'hash_indicators_count': len(self.hash_indicators)
        }
    
    def cleanup_expired_indicators(self):
        """Очищает истекшие индикаторы угроз"""
        try:
            expired_indicators = [
                indicator_id for indicator_id, indicator in self.indicators.items()
                if indicator.is_expired(self.config['max_age_days'])
            ]
            
            for indicator_id in expired_indicators:
                self.remove_indicator(indicator_id)
            
            if expired_indicators:
                self.logger.info(f"Cleaned up {len(expired_indicators)} expired indicators")
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup expired indicators: {e}")
    
    def export_indicators(self, format: str = "json") -> str:
        """Экспортирует индикаторы угроз"""
        try:
            if format.lower() == "json":
                return json.dumps(
                    [indicator.to_dict() for indicator in self.indicators.values()],
                    indent=2,
                    ensure_ascii=False
                )
            elif format.lower() == "yaml" and yaml:
                return yaml.dump(
                    [indicator.to_dict() for indicator in self.indicators.values()],
                    default_flow_style=False,
                    allow_unicode=True
                )
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"Failed to export indicators: {e}")
            raise


# Глобальный экземпляр сервиса угроз
threat_intelligence_service = ThreatIntelligenceService()


async def check_threat(event: Dict[str, Any]) -> Optional[ThreatReport]:
    """Удобная функция для проверки угроз"""
    return await threat_intelligence_service.check_threat(event)


def get_threat_intelligence_service() -> ThreatIntelligenceService:
    """Возвращает глобальный экземпляр сервиса угроз"""
    return threat_intelligence_service
