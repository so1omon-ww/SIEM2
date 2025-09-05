"""
Система действий по алертам безопасности
Поддерживает различные типы атак и меры противодействия
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import subprocess
import json
import logging

logger = logging.getLogger(__name__)

class AlertType(Enum):
    """Типы алертов безопасности"""
    DDOS_SYN_FLOOD = "ddos_syn_flood"
    DDOS_HTTP_RPS = "ddos_http_rps"
    PORT_SCAN = "port_scan"
    BRUTEFORCE_SSH = "bruteforce_ssh"
    BRUTEFORCE_HTTP = "bruteforce_http"
    ARP_SPOOF = "arp_spoof"
    ARP_FLOOD = "arp_flood"
    DNS_NXDOMAIN_FLOOD = "dns_nxdomain_flood"
    DNS_RANDOM_SUBDOMAINS = "dns_random_subdomains"
    LATERAL_MOVEMENT = "lateral_movement"
    ANOMALY_DETECTION = "anomaly_detection"

class ActionType(Enum):
    """Типы действий по алертам"""
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ISOLATE_HOST = "isolate_host"
    RESTART_SERVICE = "restart_service"
    FLUSH_CACHE = "flush_cache"
    NOTIFY_ADMIN = "notify_admin"
    LOG_EVENT = "log_event"
    CUSTOM_SCRIPT = "custom_script"

class ActionSeverity(Enum):
    """Уровни серьезности действий"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AlertContext:
    """Контекст алерта для принятия решений"""
    alert_type: AlertType
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None
    source_port: Optional[int] = None
    target_port: Optional[int] = None
    protocol: Optional[str] = None
    user: Optional[str] = None
    domain: Optional[str] = None
    mac_address: Optional[str] = None
    severity: ActionSeverity = ActionSeverity.MEDIUM
    confidence: float = 0.8
    timestamp: datetime = None
    additional_data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.additional_data is None:
            self.additional_data = {}

@dataclass
class ActionConfig:
    """Конфигурация действия"""
    action_type: ActionType
    enabled: bool = True
    auto_execute: bool = False
    ttl_minutes: int = 60
    parameters: Dict[str, Any] = None
    conditions: List[str] = None  # Условия для выполнения
    
    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.conditions is None:
            self.conditions = []

class AlertActionEngine:
    """Движок выполнения действий по алертам"""
    
    def __init__(self):
        self.action_configs: Dict[AlertType, List[ActionConfig]] = {}
        self.active_blocks: Dict[str, datetime] = {}  # IP -> время блокировки
        self.action_history: List[Dict] = []
        self._setup_default_actions()
    
    def _setup_default_actions(self):
        """Настройка действий по умолчанию для каждого типа алерта"""
        
        # DDoS атаки
        self.action_configs[AlertType.DDOS_SYN_FLOOD] = [
            ActionConfig(
                action_type=ActionType.RATE_LIMIT,
                auto_execute=True,
                ttl_minutes=30,
                parameters={"max_connections_per_second": 10}
            ),
            ActionConfig(
                action_type=ActionType.BLOCK_IP,
                auto_execute=False,  # Требует подтверждения
                ttl_minutes=60,
                conditions=["confidence > 0.9"]
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        self.action_configs[AlertType.DDOS_HTTP_RPS] = [
            ActionConfig(
                action_type=ActionType.RATE_LIMIT,
                auto_execute=True,
                ttl_minutes=15,
                parameters={"max_requests_per_second": 50}
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        # Сканирование портов
        self.action_configs[AlertType.PORT_SCAN] = [
            ActionConfig(
                action_type=ActionType.BLOCK_IP,
                auto_execute=True,
                ttl_minutes=120,
                conditions=["confidence > 0.8"]
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        # Брутфорс атаки
        self.action_configs[AlertType.BRUTEFORCE_SSH] = [
            ActionConfig(
                action_type=ActionType.BLOCK_IP,
                auto_execute=True,
                ttl_minutes=180,
                conditions=["confidence > 0.7"]
            ),
            ActionConfig(
                action_type=ActionType.RESTART_SERVICE,
                auto_execute=False,
                parameters={"service": "ssh"}
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        self.action_configs[AlertType.BRUTEFORCE_HTTP] = [
            ActionConfig(
                action_type=ActionType.RATE_LIMIT,
                auto_execute=True,
                ttl_minutes=60,
                parameters={"max_requests_per_minute": 10}
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        # ARP атаки
        self.action_configs[AlertType.ARP_SPOOF] = [
            ActionConfig(
                action_type=ActionType.ISOLATE_HOST,
                auto_execute=True,
                ttl_minutes=300,
                conditions=["confidence > 0.9"]
            ),
            ActionConfig(
                action_type=ActionType.FLUSH_CACHE,
                auto_execute=True,
                parameters={"cache_type": "arp"}
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        self.action_configs[AlertType.ARP_FLOOD] = [
            ActionConfig(
                action_type=ActionType.ISOLATE_HOST,
                auto_execute=True,
                ttl_minutes=60
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        # DNS атаки
        self.action_configs[AlertType.DNS_NXDOMAIN_FLOOD] = [
            ActionConfig(
                action_type=ActionType.RATE_LIMIT,
                auto_execute=True,
                ttl_minutes=30,
                parameters={"max_queries_per_second": 20}
            ),
            ActionConfig(
                action_type=ActionType.RESTART_SERVICE,
                auto_execute=False,
                parameters={"service": "named"}
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        self.action_configs[AlertType.DNS_RANDOM_SUBDOMAINS] = [
            ActionConfig(
                action_type=ActionType.BLOCK_IP,
                auto_execute=True,
                ttl_minutes=90
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        # Другие типы алертов
        self.action_configs[AlertType.LATERAL_MOVEMENT] = [
            ActionConfig(
                action_type=ActionType.ISOLATE_HOST,
                auto_execute=False,  # Требует ручного подтверждения
                ttl_minutes=1440  # 24 часа
            ),
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            )
        ]
        
        self.action_configs[AlertType.ANOMALY_DETECTION] = [
            ActionConfig(
                action_type=ActionType.NOTIFY_ADMIN,
                auto_execute=True
            ),
            ActionConfig(
                action_type=ActionType.LOG_EVENT,
                auto_execute=True
            )
        ]
    
    async def process_alert(self, context: AlertContext) -> List[Dict]:
        """Обработка алерта и выполнение соответствующих действий"""
        actions_performed = []
        
        if context.alert_type not in self.action_configs:
            logger.warning(f"No action config for alert type: {context.alert_type}")
            return actions_performed
        
        configs = self.action_configs[context.alert_type]
        
        for config in configs:
            if not config.enabled:
                continue
                
            # Проверяем условия выполнения
            if not self._check_conditions(config, context):
                continue
            
            # Выполняем действие
            try:
                if config.auto_execute:
                    result = await self._execute_action(config, context)
                    actions_performed.append(result)
                else:
                    # Добавляем в очередь для ручного подтверждения
                    await self._queue_for_approval(config, context)
                    
            except Exception as e:
                logger.error(f"Error executing action {config.action_type}: {e}")
                actions_performed.append({
                    "action": config.action_type.value,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return actions_performed
    
    def _check_conditions(self, config: ActionConfig, context: AlertContext) -> bool:
        """Проверка условий для выполнения действия"""
        if not config.conditions:
            return True
        
        for condition in config.conditions:
            if not self._evaluate_condition(condition, context):
                return False
        
        return True
    
    def _evaluate_condition(self, condition: str, context: AlertContext) -> bool:
        """Вычисление условия (простая реализация)"""
        try:
            # Подставляем значения из контекста
            local_vars = {
                'confidence': context.confidence,
                'severity': context.severity.value,
                'source_ip': context.source_ip,
                'target_ip': context.target_ip
            }
            return eval(condition, {"__builtins__": {}}, local_vars)
        except:
            return False
    
    async def _execute_action(self, config: ActionConfig, context: AlertContext) -> Dict:
        """Выполнение конкретного действия"""
        action_result = {
            "action": config.action_type.value,
            "context": {
                "alert_type": context.alert_type.value,
                "source_ip": context.source_ip,
                "target_ip": context.target_ip,
                "severity": context.severity.value
            },
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }
        
        try:
            if config.action_type == ActionType.BLOCK_IP:
                await self._block_ip(context.source_ip, config.ttl_minutes)
                action_result["details"] = f"Blocked IP {context.source_ip} for {config.ttl_minutes} minutes"
                
            elif config.action_type == ActionType.RATE_LIMIT:
                await self._apply_rate_limit(context, config.parameters)
                action_result["details"] = f"Applied rate limiting: {config.parameters}"
                
            elif config.action_type == ActionType.ISOLATE_HOST:
                await self._isolate_host(context.source_ip, config.ttl_minutes)
                action_result["details"] = f"Isolated host {context.source_ip} for {config.ttl_minutes} minutes"
                
            elif config.action_type == ActionType.RESTART_SERVICE:
                await self._restart_service(config.parameters.get("service"))
                action_result["details"] = f"Restarted service: {config.parameters.get('service')}"
                
            elif config.action_type == ActionType.FLUSH_CACHE:
                await self._flush_cache(config.parameters.get("cache_type"))
                action_result["details"] = f"Flushed {config.parameters.get('cache_type')} cache"
                
            elif config.action_type == ActionType.NOTIFY_ADMIN:
                await self._notify_admin(context)
                action_result["details"] = "Admin notification sent"
                
            elif config.action_type == ActionType.LOG_EVENT:
                await self._log_event(context)
                action_result["details"] = "Event logged"
                
            elif config.action_type == ActionType.CUSTOM_SCRIPT:
                await self._run_custom_script(config.parameters, context)
                action_result["details"] = f"Custom script executed: {config.parameters.get('script')}"
        
        except Exception as e:
            action_result["status"] = "error"
            action_result["error"] = str(e)
        
        # Сохраняем в историю
        self.action_history.append(action_result)
        
        return action_result
    
    async def _block_ip(self, ip: str, ttl_minutes: int):
        """Блокировка IP адреса"""
        if not ip:
            return
        
        # Добавляем правило в iptables
        cmd = [
            "sudo", "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.active_blocks[ip] = datetime.now() + timedelta(minutes=ttl_minutes)
                logger.info(f"Blocked IP {ip} for {ttl_minutes} minutes")
            else:
                logger.error(f"Failed to block IP {ip}: {result.stderr}")
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout blocking IP {ip}")
        except Exception as e:
            logger.error(f"Error blocking IP {ip}: {e}")
    
    async def _apply_rate_limit(self, context: AlertContext, parameters: Dict):
        """Применение ограничений скорости"""
        # Здесь можно интегрироваться с nginx, haproxy, или другими системами
        logger.info(f"Applied rate limiting for {context.source_ip}: {parameters}")
    
    async def _isolate_host(self, ip: str, ttl_minutes: int):
        """Изоляция хоста (перевод в карантинный VLAN)"""
        # Здесь можно интегрироваться с сетевым оборудованием
        logger.info(f"Isolated host {ip} for {ttl_minutes} minutes")
    
    async def _restart_service(self, service: str):
        """Перезапуск сервиса"""
        if not service:
            return
        
        cmd = ["sudo", "systemctl", "restart", service]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"Restarted service {service}")
            else:
                logger.error(f"Failed to restart service {service}: {result.stderr}")
        except Exception as e:
            logger.error(f"Error restarting service {service}: {e}")
    
    async def _flush_cache(self, cache_type: str):
        """Очистка кеша"""
        if cache_type == "arp":
            cmd = ["sudo", "ip", "-s", "-s", "neigh", "flush", "all"]
        elif cache_type == "dns":
            cmd = ["sudo", "systemctl", "restart", "systemd-resolved"]
        else:
            logger.warning(f"Unknown cache type: {cache_type}")
            return
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                logger.info(f"Flushed {cache_type} cache")
            else:
                logger.error(f"Failed to flush {cache_type} cache: {result.stderr}")
        except Exception as e:
            logger.error(f"Error flushing {cache_type} cache: {e}")
    
    async def _notify_admin(self, context: AlertContext):
        """Уведомление администратора"""
        # Здесь можно интегрироваться с Slack, Telegram, email и т.д.
        logger.warning(f"SECURITY ALERT: {context.alert_type.value} from {context.source_ip}")
    
    async def _log_event(self, context: AlertContext):
        """Логирование события"""
        event_data = {
            "timestamp": context.timestamp.isoformat(),
            "alert_type": context.alert_type.value,
            "source_ip": context.source_ip,
            "target_ip": context.target_ip,
            "severity": context.severity.value,
            "confidence": context.confidence,
            "additional_data": context.additional_data
        }
        logger.info(f"Security event logged: {json.dumps(event_data)}")
    
    async def _run_custom_script(self, parameters: Dict, context: AlertContext):
        """Выполнение пользовательского скрипта"""
        script_path = parameters.get("script")
        if not script_path:
            return
        
        # Передаем контекст в скрипт через переменные окружения
        env = {
            "ALERT_TYPE": context.alert_type.value,
            "SOURCE_IP": context.source_ip or "",
            "TARGET_IP": context.target_ip or "",
            "SEVERITY": context.severity.value,
            "CONFIDENCE": str(context.confidence)
        }
        
        try:
            result = subprocess.run(
                [script_path], 
                capture_output=True, 
                text=True, 
                timeout=60,
                env=env
            )
            if result.returncode == 0:
                logger.info(f"Custom script {script_path} executed successfully")
            else:
                logger.error(f"Custom script {script_path} failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running custom script {script_path}: {e}")
    
    async def _queue_for_approval(self, config: ActionConfig, context: AlertContext):
        """Добавление действия в очередь для ручного подтверждения"""
        # Здесь можно интегрироваться с системой уведомлений
        logger.info(f"Action {config.action_type.value} queued for approval")
    
    def get_pending_actions(self) -> List[Dict]:
        """Получение списка действий, ожидающих подтверждения"""
        # В реальной реализации здесь будет запрос к БД
        # Пока что возвращаем пустой список
        return []
    
    def approve_action(self, action_id: str) -> bool:
        """Подтверждение выполнения действия"""
        # В реальной реализации здесь будет обновление статуса в БД
        # Пока что просто возвращаем True
        logger.info(f"Action {action_id} approved")
        return True
    
    def get_action_history(self, limit: int = 100) -> List[Dict]:
        """Получение истории выполненных действий"""
        return self.action_history[-limit:]
    
    def cleanup_expired_blocks(self):
        """Очистка истекших блокировок"""
        now = datetime.now()
        expired_ips = [
            ip for ip, expiry in self.active_blocks.items() 
            if expiry <= now
        ]
        
        for ip in expired_ips:
            try:
                # Удаляем правило из iptables
                cmd = ["sudo", "iptables", "-D", "INPUT", "-s", ip, "-j", "DROP"]
                subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                del self.active_blocks[ip]
                logger.info(f"Unblocked IP {ip}")
            except Exception as e:
                logger.error(f"Error unblocking IP {ip}: {e}")

# Глобальный экземпляр движка действий
alert_action_engine = AlertActionEngine()

