from fastapi import APIRouter, HTTPException, Query, Header, Depends
from sqlalchemy.orm import Session
from ...common.db import get_session
from ..repositories.events_repo import list_recent_by_owner
from ..repositories.alerts_repo import list_recent_alerts_by_owner
# from ..repositories.users_repo import get_user_by_id  # Не используется
from ..services.auth_service import get_user_id_by_api_key
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

router = APIRouter()

@router.get("/stats", summary="Dashboard Statistics")
def get_dashboard_stats(
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Получить статистику для дашборда"""
    try:
        # Получаем пользователя по API ключу
        user_id = get_user_id_by_api_key(x_api_key)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # user_id уже int, не нужно конвертировать
        
        # Получаем события за последние 24 часа
        with get_session() as db:
            events = list_recent_by_owner(db, owner_id=user_id, limit=1000)
            alerts = list_recent_alerts_by_owner(db, owner_id=user_id, limit=1000)
        
        # Фильтруем события за последние 24 часа
        now = datetime.utcnow().replace(tzinfo=None)
        last_24h = now - timedelta(hours=24)
        
        recent_events = []
        for event in events:
            ts = event.get('ts')
            if ts:
                if isinstance(ts, str):
                    event_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    event_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                if event_time > last_24h:
                    recent_events.append(event)
        
        recent_alerts = []
        for alert in alerts:
            ts = alert.get('ts')
            if ts:
                if isinstance(ts, str):
                    alert_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    alert_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                if alert_time > last_24h:
                    recent_alerts.append(alert)
        
        # Подсчитываем статистику
        critical_alerts = [alert for alert in recent_alerts if alert.get('severity') == 'critical']
        
        # Уникальные хосты
        unique_hosts = set()
        for event in recent_events:
            if event.get('host_id'):
                unique_hosts.add(event['host_id'])
        
        # Уникальные IP адреса
        unique_ips = set()
        for event in recent_events:
            # Проверяем src_ip и dst_ip
            if event.get('src_ip'):
                unique_ips.add(event['src_ip'])
            if event.get('dst_ip'):
                unique_ips.add(event['dst_ip'])
            
            # Проверяем IP адреса в details.connection
            details = event.get('details', {})
            if isinstance(details, dict):
                connection = details.get('connection', {})
                if isinstance(connection, dict):
                    local_addr = connection.get('local_addr')
                    if local_addr and ':' in local_addr:
                        ip = local_addr.split(':')[0]
                        unique_ips.add(ip)
                    remote_addr = connection.get('remote_addr')
                    if remote_addr and ':' in remote_addr:
                        ip = remote_addr.split(':')[0]
                        unique_ips.add(ip)
        
        # События угроз
        threat_events = [
            event for event in recent_events
            if any(keyword in event.get('event_type', '').lower() 
                   for keyword in ['threat', 'suspicious', 'attack', 'blocked', 'scan'])
        ]
        
        # Активные соединения (сетевые события)
        active_connections = len([
            event for event in recent_events 
            if event.get('event_type') == 'network.connection'
        ])
        
        # Общий трафик (на основе системных метрик)
        total_traffic_bytes = 0
        for event in recent_events:
            if event.get('event_type') == 'system.performance':
                details = event.get('details', {})
                if isinstance(details, dict):
                    performance = details.get('performance', {})
                    if isinstance(performance, dict):
                        # Получаем сетевой трафик в байтах
                        network_sent = performance.get('network_sent_mb', 0) * 1024 * 1024
                        network_recv = performance.get('network_recv_mb', 0) * 1024 * 1024
                        total_traffic_bytes += network_sent + network_recv
        
        # Здоровье системы (на основе системных метрик)
        system_health = 100  # Базовое значение
        performance_events = [
            event for event in recent_events 
            if event.get('event_type') == 'system.performance'
        ]
        
        if performance_events:
            latest_performance = performance_events[0]
            details = latest_performance.get('details', {})
            performance = details.get('performance', {})
            
            # Рассчитываем здоровье системы на основе метрик
            cpu = performance.get('cpu_percent', 0)
            memory = performance.get('memory_percent', 0)
            disk = performance.get('disk_percent', 0)
            
            # Если любая метрика критична, снижаем здоровье системы
            if cpu > 90 or memory > 95 or disk > 95:
                system_health = 50
            elif cpu > 80 or memory > 90 or disk > 90:
                system_health = 75
        
        stats = {
            "activeEvents": len(recent_events),
            "blockedThreats": len(threat_events),
            "criticalAlerts": len(critical_alerts),
            "protectedSystems": len(unique_hosts),
            "totalTraffic": total_traffic_bytes,
            "uniqueIPs": len(unique_ips),
            "activeConnections": active_connections,
            "systemHealth": system_health
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")

@router.get("/threat-types", summary="Threat Types Distribution")
def get_threat_types(
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Получить распределение типов угроз"""
    try:
        user_id = get_user_id_by_api_key(x_api_key)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # user_id уже int, не нужно конвертировать
        
        with get_session() as db:
            events = list_recent_by_owner(db, owner_id=user_id, limit=1000)
        
        # Фильтруем события за последние 24 часа
        now = datetime.utcnow().replace(tzinfo=None)
        last_24h = now - timedelta(hours=24)
        
        recent_events = []
        for event in events:
            ts = event.get('ts')
            if ts:
                if isinstance(ts, str):
                    event_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    event_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                if event_time > last_24h:
                    recent_events.append(event)
        
        # Группируем по типам угроз
        threat_types = {}
        for event in recent_events:
            event_type = event.get('event_type', 'unknown')
            
            # Определяем тип угрозы на основе типа события
            if 'network.connection' in event_type:
                threat_type = 'Подозрительный трафик'
            elif 'process.created' in event_type:
                threat_type = 'Аномальная активность'
            elif 'system.performance' in event_type:
                continue  # Пропускаем системные метрики
            elif 'scan' in event_type.lower():
                threat_type = 'Сканирование портов'
            elif 'attack' in event_type.lower():
                threat_type = 'Попытки вторжения'
            elif 'ddos' in event_type.lower():
                threat_type = 'DDoS атаки'
            elif 'phishing' in event_type.lower():
                threat_type = 'Фишинг'
            else:
                threat_type = 'Другие угрозы'
            
            threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        
        # Конвертируем в нужный формат
        total_threats = sum(threat_types.values())
        result = []
        
        colors = ['#ef4444', '#f97316', '#eab308', '#06b6d4', '#8b5cf6', '#ec4899']
        
        for i, (threat_type, count) in enumerate(sorted(threat_types.items(), key=lambda x: x[1], reverse=True)):
            percentage = round((count / total_threats * 100) if total_threats > 0 else 0, 1)
            result.append({
                "name": threat_type,
                "value": percentage,
                "color": colors[i % len(colors)],
                "trend": "+0%"  # Пока без трендов
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting threat types: {str(e)}")

@router.get("/time-activity", summary="Activity Over Time")
def get_time_activity(
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Получить активность по времени"""
    try:
        user_id = get_user_id_by_api_key(x_api_key)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # user_id уже int, не нужно конвертировать
        
        with get_session() as db:
            events = list_recent_by_owner(db, owner_id=user_id, limit=1000)
        
        # Фильтруем события за последние 24 часа
        now = datetime.utcnow().replace(tzinfo=None)
        last_24h = now - timedelta(hours=24)
        
        recent_events = []
        for event in events:
            ts = event.get('ts')
            if ts:
                if isinstance(ts, str):
                    event_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    event_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                if event_time > last_24h:
                    recent_events.append(event)
        
        # Группируем по часам
        hourly_activity = []
        for hour in range(24):
            hour_start = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)
            
            hour_events = []
            for event in recent_events:
                ts = event.get('ts')
                if ts:
                    if isinstance(ts, str):
                        event_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                    else:
                        event_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                    if hour_start <= event_time < hour_end:
                        hour_events.append(event)
            
            threat_events = [
                event for event in hour_events
                if any(keyword in event.get('event_type', '').lower() 
                       for keyword in ['threat', 'suspicious', 'attack', 'scan'])
            ]
            
            blocked_events = [
                event for event in hour_events
                if 'blocked' in event.get('event_type', '').lower()
            ]
            
            hourly_activity.append({
                "hour": f"{hour:02d}:00",
                "events": len(hour_events),
                "threats": len(threat_events),
                "blocked": len(blocked_events)
            })
        
        return hourly_activity
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting time activity: {str(e)}")

@router.get("/top-threats", summary="Top Threats")
def get_top_threats(
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Получить топ угроз"""
    try:
        user_id = get_user_id_by_api_key(x_api_key)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # user_id уже int, не нужно конвертировать
        
        with get_session() as db:
            events = list_recent_by_owner(db, owner_id=user_id, limit=1000)
        
        # Фильтруем события за последние 24 часа
        now = datetime.utcnow().replace(tzinfo=None)
        last_24h = now - timedelta(hours=24)
        
        recent_events = []
        for event in events:
            ts = event.get('ts')
            if ts:
                if isinstance(ts, str):
                    event_time = datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
                else:
                    event_time = ts.replace(tzinfo=None) if ts.tzinfo else ts
                if event_time > last_24h:
                    recent_events.append(event)
        
        # Группируем по типам событий
        threat_counts = {}
        for event in recent_events:
            event_type = event.get('event_type', 'unknown')
            
            # Пропускаем системные метрики
            if 'system.performance' in event_type:
                continue
                
            threat_counts[event_type] = threat_counts.get(event_type, 0) + 1
        
        # Сортируем и ограничиваем топ
        top_threats = []
        for i, (event_type, count) in enumerate(sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:8]):
            severity = 'high' if count > 10 else 'medium' if count > 5 else 'low'
            top_threats.append({
                "id": i + 1,
                "type": event_type.replace('_', ' ').replace('.', ' ').title(),
                "count": count,
                "severity": severity,
                "trend": "+0%"  # Пока без трендов
            })
        
        return top_threats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting top threats: {str(e)}")

@router.get("/recent-events", summary="Recent Events for Dashboard")
def get_recent_events(
    limit: int = Query(5, ge=1, le=20),
    x_api_key: str = Header(..., alias="X-API-Key")
):
    """Получить последние события для дашборда"""
    try:
        user_id = get_user_id_by_api_key(x_api_key)
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        # user_id уже int, не нужно конвертировать
        
        with get_session() as db:
            events = list_recent_by_owner(db, owner_id=user_id, limit=limit)
        
        # Форматируем события для дашборда
        formatted_events = []
        for event in events:
            event_type = event.get('event_type', 'unknown')
            timestamp = event.get('ts', '')
            
            # Определяем описание события
            if 'network.connection' in event_type:
                description = "Обнаружена подозрительная активность"
                src_ip = event.get('src_ip', 'Unknown')
            elif 'process.created' in event_type:
                description = "Создан новый процесс"
                src_ip = event.get('host_id', 'Unknown')
            elif 'system.performance' in event_type:
                description = "Обновление системных метрик"
                src_ip = event.get('host_id', 'Unknown')
            else:
                description = f"Событие: {event_type}"
                src_ip = event.get('src_ip', event.get('host_id', 'Unknown'))
            
            formatted_events.append({
                "description": description,
                "src_ip": src_ip,
                "timestamp": timestamp,
                "severity": event.get('severity', 'info')
            })
        
        return formatted_events
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recent events: {str(e)}")
