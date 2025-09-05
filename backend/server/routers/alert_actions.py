"""
API endpoints для управления действиями по алертам безопасности
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from ..deps import get_current_user
from ...analyzer.engine.alert_actions import (
    AlertActionEngine, AlertContext, AlertType, ActionType, 
    ActionSeverity, ActionConfig, alert_action_engine
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic модели для API
class AlertContextRequest(BaseModel):
    alert_type: str
    source_ip: Optional[str] = None
    target_ip: Optional[str] = None
    source_port: Optional[int] = None
    target_port: Optional[int] = None
    protocol: Optional[str] = None
    user: Optional[str] = None
    domain: Optional[str] = None
    mac_address: Optional[str] = None
    severity: str = "medium"
    confidence: float = 0.8
    additional_data: Optional[Dict[str, Any]] = None

class ActionConfigRequest(BaseModel):
    action_type: str
    enabled: bool = True
    auto_execute: bool = False
    ttl_minutes: int = 60
    parameters: Optional[Dict[str, Any]] = None
    conditions: Optional[List[str]] = None

class ActionResponse(BaseModel):
    action: str
    status: str
    details: Optional[str] = None
    timestamp: str
    error: Optional[str] = None

@router.post("/process-alert", response_model=List[ActionResponse])
async def process_alert(
    alert_context: AlertContextRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Обработка алерта и выполнение соответствующих действий"""
    try:
        # Преобразуем строковые значения в enum
        alert_type = AlertType(alert_context.alert_type)
        severity = ActionSeverity(alert_context.severity)
        
        # Создаем контекст алерта
        context = AlertContext(
            alert_type=alert_type,
            source_ip=alert_context.source_ip,
            target_ip=alert_context.target_ip,
            source_port=alert_context.source_port,
            target_port=alert_context.target_port,
            protocol=alert_context.protocol,
            user=alert_context.user,
            domain=alert_context.domain,
            mac_address=alert_context.mac_address,
            severity=severity,
            confidence=alert_context.confidence,
            additional_data=alert_context.additional_data or {}
        )
        
        # Обрабатываем алерт
        actions = await alert_action_engine.process_alert(context)
        
        return actions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid alert type or severity: {e}")
    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get("/action-types")
async def get_action_types(current_user: dict = Depends(get_current_user)):
    """Получение списка доступных типов действий"""
    return {
        "action_types": [action_type.value for action_type in ActionType],
        "alert_types": [alert_type.value for alert_type in AlertType],
        "severity_levels": [severity.value for severity in ActionSeverity]
    }

@router.get("/action-configs")
async def get_action_configs(current_user: dict = Depends(get_current_user)):
    """Получение текущих конфигураций действий"""
    configs = {}
    for alert_type, action_configs in alert_action_engine.action_configs.items():
        configs[alert_type.value] = [
            {
                "action_type": config.action_type.value,
                "enabled": config.enabled,
                "auto_execute": config.auto_execute,
                "ttl_minutes": config.ttl_minutes,
                "parameters": config.parameters,
                "conditions": config.conditions
            }
            for config in action_configs
        ]
    return configs

@router.put("/action-configs/{alert_type}")
async def update_action_configs(
    alert_type: str,
    configs: List[ActionConfigRequest],
    current_user: dict = Depends(get_current_user)
):
    """Обновление конфигураций действий для типа алерта"""
    try:
        alert_type_enum = AlertType(alert_type)
        
        # Преобразуем запросы в объекты конфигурации
        action_configs = []
        for config_req in configs:
            action_type = ActionType(config_req.action_type)
            config = ActionConfig(
                action_type=action_type,
                enabled=config_req.enabled,
                auto_execute=config_req.auto_execute,
                ttl_minutes=config_req.ttl_minutes,
                parameters=config_req.parameters or {},
                conditions=config_req.conditions or []
            )
            action_configs.append(config)
        
        # Обновляем конфигурацию
        alert_action_engine.action_configs[alert_type_enum] = action_configs
        
        return {"message": f"Action configs updated for {alert_type}"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid alert type or action type: {e}")
    except Exception as e:
        logger.error(f"Error updating action configs: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.get("/pending-actions")
async def get_pending_actions(current_user: dict = Depends(get_current_user)):
    """Получение списка действий, ожидающих подтверждения"""
    return alert_action_engine.get_pending_actions()

@router.post("/approve-action/{action_id}")
async def approve_action(
    action_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Подтверждение выполнения действия"""
    success = alert_action_engine.approve_action(action_id)
    if success:
        return {"message": f"Action {action_id} approved"}
    else:
        raise HTTPException(status_code=404, detail="Action not found")

@router.get("/action-history")
async def get_action_history(
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Получение истории выполненных действий"""
    return alert_action_engine.get_action_history(limit)

@router.get("/active-blocks")
async def get_active_blocks(current_user: dict = Depends(get_current_user)):
    """Получение списка активных блокировок IP"""
    return {
        "active_blocks": [
            {
                "ip": ip,
                "expires_at": expiry.isoformat(),
                "remaining_minutes": int((expiry - datetime.now()).total_seconds() / 60)
            }
            for ip, expiry in alert_action_engine.active_blocks.items()
        ]
    }

@router.delete("/unblock-ip/{ip}")
async def unblock_ip(
    ip: str,
    current_user: dict = Depends(get_current_user)
):
    """Разблокировка IP адреса"""
    try:
        if ip in alert_action_engine.active_blocks:
            del alert_action_engine.active_blocks[ip]
            return {"message": f"IP {ip} unblocked"}
        else:
            raise HTTPException(status_code=404, detail="IP not found in active blocks")
    except Exception as e:
        logger.error(f"Error unblocking IP {ip}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

@router.post("/cleanup-expired-blocks")
async def cleanup_expired_blocks(
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Очистка истекших блокировок"""
    background_tasks.add_task(alert_action_engine.cleanup_expired_blocks)
    return {"message": "Cleanup task scheduled"}

@router.get("/attack-patterns")
async def get_attack_patterns(current_user: dict = Depends(get_current_user)):
    """Получение описаний паттернов атак и мер противодействия"""
    return {
        "ddos": {
            "syn_flood": {
                "description": "DDoS атака с использованием SYN-флуда",
                "signs": [
                    "Резкий всплеск TCP SYN пакетов",
                    "Высокое отношение SYN/SYN-ACK",
                    "Множество полуоткрытых соединений",
                    "Аномальное время (ночь, выходные)"
                ],
                "countermeasures": [
                    "Ограничение новых соединений с одного IP",
                    "Включение SYN cookies",
                    "Использование CDN/анти-DDoS сервисов",
                    "Блокировка подозрительных IP"
                ]
            },
            "http_rps": {
                "description": "DDoS атака на HTTP сервисы",
                "signs": [
                    "Аномально высокий RPS с одного IP",
                    "Повторяющиеся запросы к одному эндпоинту",
                    "Рост ошибок 503/429",
                    "Снижение производительности сервера"
                ],
                "countermeasures": [
                    "Rate limiting на уровне веб-сервера",
                    "Кэширование статического контента",
                    "Блокировка по User-Agent",
                    "Использование CAPTCHA"
                ]
            }
        },
        "port_scan": {
            "description": "Сканирование портов для поиска уязвимостей",
            "signs": [
                "Множество портов с одного IP за короткое время",
                "Последовательные попытки подключения",
                "SYN без завершения соединения",
                "Горизонтальное сканирование (один порт, много хостов)"
            ],
            "countermeasures": [
                "Автоматическая блокировка сканирующих IP",
                "Минимизация открытых портов",
                "Использование honeypots",
                "Мониторинг и оповещения"
            ]
        },
        "bruteforce": {
            "ssh": {
                "description": "Подбор паролей для SSH",
                "signs": [
                    "Множество неудачных попыток входа",
                    "Перебор разных пользователей",
                    "Частые блокировки аккаунтов",
                    "Логины в нестандартное время"
                ],
                "countermeasures": [
                    "Fail2Ban для автоматической блокировки",
                    "Ограничение попыток входа",
                    "Использование ключей вместо паролей",
                    "Многофакторная аутентификация"
                ]
            },
            "http": {
                "description": "Подбор паролей для веб-приложений",
                "signs": [
                    "Множество HTTP 401/403 ошибок",
                    "Повторяющиеся POST запросы к /login",
                    "Использование словарей паролей",
                    "Аномальная активность с одного IP"
                ],
                "countermeasures": [
                    "Rate limiting на уровне приложения",
                    "CAPTCHA после нескольких неудач",
                    "Блокировка по IP после N попыток",
                    "Усиление политик паролей"
                ]
            }
        },
        "arp_spoof": {
            "description": "ARP-спуфинг для перехвата трафика",
            "signs": [
                "Дубли в ARP-таблице (один MAC для разных IP)",
                "Внезапная смена MAC-адреса для IP",
                "Аномальная ARP-активность",
                "ARP-флуд в сети"
            ],
                "countermeasures": [
                "Dynamic ARP Inspection на коммутаторах",
                "Статические ARP-записи для критичных узлов",
                "Мониторинг ARP-таблиц",
                "Изоляция подозрительных устройств"
            ]
        },
        "dns_attacks": {
            "nxdomain_flood": {
                "description": "DDoS атака на DNS с NXDOMAIN ответами",
                "signs": [
                    "Множество NXDOMAIN ответов",
                    "Запросы к несуществующим доменам",
                    "Перегрузка DNS-сервера",
                    "Снижение производительности DNS"
                ],
                "countermeasures": [
                    "Rate limiting на DNS-сервере",
                    "Кэширование NXDOMAIN ответов",
                    "Фильтрация подозрительных запросов",
                    "Использование Anycast DNS"
                ]
            },
            "random_subdomains": {
                "description": "Генерация случайных поддоменов для обхода фильтров",
                "signs": [
                    "Высокая энтропия в именах доменов",
                    "Длинные случайные поддомены",
                    "Массовые запросы к поддоменам",
                    "Попытки обхода blacklist"
                ],
                "countermeasures": [
                    "Анализ энтропии доменных имен",
                    "Блокировка по паттернам",
                    "Использование wildcard DNS",
                    "Мониторинг аномальной DNS-активности"
                ]
            }
        }
    }

@router.get("/recommendations/{alert_type}")
async def get_recommendations(
    alert_type: str,
    current_user: dict = Depends(get_current_user)
):
    """Получение рекомендаций по противодействию для конкретного типа алерта"""
    try:
        alert_type_enum = AlertType(alert_type)
        patterns = await get_attack_patterns(current_user)
        
        # Возвращаем рекомендации для конкретного типа алерта
        if alert_type_enum == AlertType.DDOS_SYN_FLOOD:
            return patterns["ddos"]["syn_flood"]
        elif alert_type_enum == AlertType.DDOS_HTTP_RPS:
            return patterns["ddos"]["http_rps"]
        elif alert_type_enum == AlertType.PORT_SCAN:
            return patterns["port_scan"]
        elif alert_type_enum == AlertType.BRUTEFORCE_SSH:
            return patterns["bruteforce"]["ssh"]
        elif alert_type_enum == AlertType.BRUTEFORCE_HTTP:
            return patterns["bruteforce"]["http"]
        elif alert_type_enum == AlertType.ARP_SPOOF:
            return patterns["arp_spoof"]
        elif alert_type_enum == AlertType.DNS_NXDOMAIN_FLOOD:
            return patterns["dns_attacks"]["nxdomain_flood"]
        elif alert_type_enum == AlertType.DNS_RANDOM_SUBDOMAINS:
            return patterns["dns_attacks"]["random_subdomains"]
        else:
            return {"message": "No specific recommendations available for this alert type"}
            
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid alert type")
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")

