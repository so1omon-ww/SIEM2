"""
Утилиты для системы анализа SIEM
"""

import re
import json
import hashlib
import ipaddress
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path


class EventMatcher:
    """Класс для сопоставления событий с правилами"""
    
    @staticmethod
    def match_event(event: Dict[str, Any], rule_matches: List[Any]) -> bool:
        """Проверить, соответствует ли событие условиям правила"""
        if not rule_matches:
            return True
        
        for match_condition in rule_matches:
            if not EventMatcher._check_single_match(event, match_condition):
                return False
        
        return True
    
    @staticmethod
    def _check_single_match(event: Dict[str, Any], match_condition: Any) -> bool:
        """Проверить одно условие сопоставления"""
        # Поддержка как словарей, так и объектов RuleMatch
        if hasattr(match_condition, 'field'):
            # Это объект RuleMatch
            field = match_condition.field
            operator = match_condition.operator
            value = match_condition.value
            case_sensitive = match_condition.case_sensitive
        else:
            # Это словарь
            field = match_condition.get('field')
            operator = match_condition.get('operator', 'eq')
            value = match_condition.get('value')
            case_sensitive = match_condition.get('case_sensitive', True)
        
        if not field:
            return False
        
        # Получить значение поля из события
        field_value = EventMatcher._get_nested_field(event, field)
        
        if field_value is None:
            return False
        
        # Применить оператор
        return EventMatcher._apply_operator(field_value, operator, value, case_sensitive)
    
    @staticmethod
    def _get_nested_field(obj: Any, field_path: str) -> Any:
        """Получить значение вложенного поля"""
        if '.' not in field_path:
            return obj.get(field_path)
        
        parts = field_path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)) and part.isdigit():
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    @staticmethod
    def _apply_operator(field_value: Any, operator: str, value: Any, case_sensitive: bool) -> bool:
        """Применить оператор сравнения"""
        if operator == 'eq':
            if isinstance(field_value, str) and isinstance(value, str):
                if not case_sensitive:
                    return field_value.lower() == value.lower()
                return field_value == value
            return field_value == value
        
        elif operator == 'ne':
            if isinstance(field_value, str) and isinstance(value, str):
                if not case_sensitive:
                    return field_value.lower() != value.lower()
                return field_value != value
            return field_value != value
        
        elif operator == 'gt':
            try:
                return float(field_value) > float(value)
            except (ValueError, TypeError):
                return False
        
        elif operator == 'gte':
            try:
                return float(field_value) >= float(value)
            except (ValueError, TypeError):
                return False
        
        elif operator == 'lt':
            try:
                return float(field_value) < float(value)
            except (ValueError, TypeError):
                return False
        
        elif operator == 'lte':
            try:
                return float(field_value) <= float(value)
            except (ValueError, TypeError):
                return False
        
        elif operator == 'in':
            if isinstance(value, (list, tuple)):
                if isinstance(field_value, str) and not case_sensitive:
                    return field_value.lower() in [v.lower() if isinstance(v, str) else v for v in value]
                return field_value in value
            return False
        
        elif operator == 'not_in':
            if isinstance(value, (list, tuple)):
                if isinstance(field_value, str) and not case_sensitive:
                    return field_value.lower() not in [v.lower() if isinstance(v, str) else v for v in value]
                return field_value not in value
            return True
        
        elif operator == 'contains':
            if isinstance(field_value, str) and isinstance(value, str):
                if not case_sensitive:
                    return value.lower() in field_value.lower()
                return value in field_value
            return False
        
        elif operator == 'not_contains':
            if isinstance(field_value, str) and isinstance(value, str):
                if not case_sensitive:
                    return value.lower() not in field_value.lower()
                return value not in field_value
            return True
        
        elif operator == 'regex':
            if isinstance(field_value, str) and isinstance(value, str):
                try:
                    flags = 0 if case_sensitive else re.IGNORECASE
                    return bool(re.search(value, field_value, flags))
                except re.error:
                    return False
            return False
        
        elif operator == 'ip_in_range':
            try:
                if isinstance(field_value, str) and isinstance(value, str):
                    ip = ipaddress.ip_address(field_value)
                    network = ipaddress.ip_network(value, strict=False)
                    return ip in network
            except ValueError:
                pass
            return False
        
        elif operator == 'exists':
            return field_value is not None and field_value != ""
        
        elif operator == 'not_exists':
            return field_value is None or field_value == ""
        
        return False


class TimeWindow:
    """Класс для работы с временными окнами"""
    
    @staticmethod
    def parse_time_window(window_str: str) -> timedelta:
        """Парсить строку временного окна"""
        if not window_str:
            return timedelta(minutes=5)
        
        # Поддерживаемые форматы: 5m, 10h, 1d, 30s
        match = re.match(r'^(\d+)([smhd])$', window_str.lower())
        if not match:
            return timedelta(minutes=5)
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == 's':
            return timedelta(seconds=amount)
        elif unit == 'm':
            return timedelta(minutes=amount)
        elif unit == 'h':
            return timedelta(hours=amount)
        elif unit == 'd':
            return timedelta(days=amount)
        
        return timedelta(minutes=5)
    
    @staticmethod
    def get_window_start(window_str: str, reference_time: Optional[datetime] = None) -> datetime:
        """Получить начало временного окна"""
        if reference_time is None:
            reference_time = datetime.utcnow()
        
        window_delta = TimeWindow.parse_time_window(window_str)
        return reference_time - window_delta
    
    @staticmethod
    def is_in_window(event_time: datetime, window_str: str, reference_time: Optional[datetime] = None) -> bool:
        """Проверить, находится ли время события в окне"""
        if reference_time is None:
            reference_time = datetime.utcnow()
        
        # Убеждаемся, что оба datetime имеют одинаковый тип временной зоны
        if event_time.tzinfo is None and reference_time.tzinfo is not None:
            # event_time naive, reference_time aware - делаем event_time aware
            event_time = event_time.replace(tzinfo=reference_time.tzinfo)
        elif event_time.tzinfo is not None and reference_time.tzinfo is None:
            # event_time aware, reference_time naive - делаем reference_time aware
            reference_time = reference_time.replace(tzinfo=event_time.tzinfo)
        
        window_start = TimeWindow.get_window_start(window_str, reference_time)
        return window_start <= event_time <= reference_time


class EventAggregator:
    """Класс для агрегации событий"""
    
    @staticmethod
    def group_events(events: List[Dict[str, Any]], group_by: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """Группировать события по указанным полям"""
        if not group_by:
            return {"default": events}
        
        grouped = {}
        
        for event in events:
            group_key = EventAggregator._create_group_key(event, group_by)
            if group_key not in grouped:
                grouped[group_key] = []
            grouped[group_key].append(event)
        
        return grouped
    
    @staticmethod
    def _create_group_key(event: Dict[str, Any], group_fields: List[str]) -> str:
        """Создать ключ группировки"""
        key_parts = []
        
        for field in group_fields:
            value = EventAggregator._get_nested_field(event, field)
            key_parts.append(str(value) if value is not None else "null")
        
        return "_".join(key_parts)
    
    @staticmethod
    def _get_nested_field(obj: Any, field_path: str) -> Any:
        """Получить значение вложенного поля"""
        if '.' not in field_path:
            return obj.get(field_path)
        
        parts = field_path.split('.')
        current = obj
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, (list, tuple)) and part.isdigit():
                try:
                    current = current[int(part)]
                except (IndexError, ValueError):
                    return None
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    @staticmethod
    def count_events(events: List[Dict[str, Any]]) -> int:
        """Подсчитать количество событий"""
        return len(events)
    
    @staticmethod
    def sum_field(events: List[Dict[str, Any]], field: str) -> float:
        """Суммировать значения поля"""
        total = 0.0
        
        for event in events:
            value = EventAggregator._get_nested_field(event, field)
            if isinstance(value, (int, float)):
                total += value
        
        return total
    
    @staticmethod
    def average_field(events: List[Dict[str, Any]], field: str) -> float:
        """Вычислить среднее значение поля"""
        values = []
        
        for event in events:
            value = EventAggregator._get_nested_field(event, field)
            if isinstance(value, (int, float)):
                values.append(value)
        
        if not values:
            return 0.0
        
        return sum(values) / len(values)
    
    @staticmethod
    def min_field(events: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Найти минимальное значение поля"""
        values = []
        
        for event in events:
            value = EventAggregator._get_nested_field(event, field)
            if isinstance(value, (int, float)):
                values.append(value)
        
        return min(values) if values else None
    
    @staticmethod
    def max_field(events: List[Dict[str, Any]], field: str) -> Optional[float]:
        """Найти максимальное значение поля"""
        values = []
        
        for event in events:
            value = EventAggregator._get_nested_field(event, field)
            if isinstance(value, (int, float)):
                values.append(value)
        
        return max(values) if values else None


class DeduplicationManager:
    """Менеджер дедупликации"""
    
    def __init__(self):
        self._dedup_cache = {}
        self._cache_ttl = {}
    
    def is_duplicate(self, dedup_key: str, ttl_seconds: int = 300) -> bool:
        """Проверить, является ли событие дубликатом"""
        now = datetime.utcnow()
        
        # Очистить устаревшие записи
        self._cleanup_expired(now)
        
        if dedup_key in self._dedup_cache:
            return True
        
        # Добавить новую запись
        self._dedup_cache[dedup_key] = now
        self._cache_ttl[dedup_key] = ttl_seconds
        
        return False
    
    def _cleanup_expired(self, now: datetime):
        """Очистить устаревшие записи"""
        expired_keys = []
        
        for key, timestamp in self._dedup_cache.items():
            ttl = self._cache_ttl.get(key, 300)
            if (now - timestamp).total_seconds() > ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._dedup_cache[key]
            if key in self._cache_ttl:
                del self._cache_ttl[key]
    
    def clear_cache(self):
        """Очистить весь кеш"""
        self._dedup_cache.clear()
        self._cache_ttl.clear()


class ContextBuilder:
    """Построитель контекста для уведомлений"""
    
    @staticmethod
    def build_context(event: Dict[str, Any], rule: Dict[str, Any], 
                     additional_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Построить контекст для уведомления"""
        context = {
            "event_type": event.get("event_type"),
            "src_ip": event.get("src_ip"),
            "dst_ip": event.get("dst_ip"),
            "timestamp": event.get("timestamp"),
            "host_id": event.get("host_id"),
            "rule_name": rule.get("name"),
            "rule_severity": rule.get("severity"),
            "rule_category": rule.get("category"),
            "description": rule.get("description", ""),
        }
        
        # Добавить детали события
        if "details" in event:
            details = event["details"]
            if isinstance(details, dict):
                for key, value in details.items():
                    context[f"details.{key}"] = value
                context["details"] = details
        
        # Добавить дополнительные данные
        if additional_data:
            context.update(additional_data)
        
        return context
    
    @staticmethod
    def format_message(template: str, context: Dict[str, Any]) -> str:
        """Форматировать сообщение с контекстом"""
        try:
            return template.format(**context)
        except KeyError as e:
            # Заменить отсутствующие переменные на значения по умолчанию
            fallback_context = {
                "src_ip": context.get("src_ip", "неизвестно"),
                "dst_ip": context.get("dst_ip", "неизвестно"),
                "process_name": context.get("details.process_name", "неизвестно"),
                "username": context.get("details.username", "неизвестно"),
                "count": context.get("count", "несколько"),
                "description": context.get("description", "событие безопасности"),
                "message": context.get("message", "обнаружено событие"),
                **context
            }
            
            try:
                return template.format(**fallback_context)
            except:
                return f"Уведомление: {context.get('event_type', 'событие')}"


class ValidationUtils:
    """Утилиты валидации"""
    
    @staticmethod
    def validate_ip_address(ip_str: str) -> bool:
        """Проверить валидность IP адреса"""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_port(port: Union[int, str]) -> bool:
        """Проверить валидность порта"""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_timestamp(timestamp: Union[str, datetime]) -> bool:
        """Проверить валидность временной метки"""
        if isinstance(timestamp, datetime):
            return True
        
        if isinstance(timestamp, str):
            try:
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return True
            except ValueError:
                pass
        
        return False
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Очистить строку от потенциально опасных символов"""
        if not isinstance(value, str):
            return str(value)
        
        # Убрать управляющие символы
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', value)
        
        # Ограничить длину
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length] + "..."
        
        return sanitized


class FileUtils:
    """Утилиты для работы с файлами"""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Создать директорию, если она не существует"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Создать безопасное имя файла"""
        # Убрать недопустимые символы
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Убрать множественные подчеркивания
        safe_name = re.sub(r'_+', '_', safe_name)
        # Убрать начальные и конечные подчеркивания
        safe_name = safe_name.strip('_')
        return safe_name or "unnamed"
    
    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
        """Вычислить хеш файла"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return ""
        
        hash_obj = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception:
            return ""
    
    @staticmethod
    def load_json_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
        """Загрузить JSON файл"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    @staticmethod
    def save_json_file(file_path: Union[str, Path], data: Dict[str, Any], 
                      indent: int = 2) -> bool:
        """Сохранить данные в JSON файл"""
        file_path = Path(file_path)
        
        try:
            # Создать директорию, если не существует
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
            return True
        except Exception:
            return False
