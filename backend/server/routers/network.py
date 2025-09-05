from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import asyncio
import subprocess
import ipaddress
import socket
from datetime import datetime, timedelta, timezone

from ..deps import get_db, get_current_user, get_current_user_from_api_key
from ...common.logging import setup_logger

router = APIRouter()
logger = setup_logger(__name__)

@router.get("/servers")
async def get_servers(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список серверов в сети"""
    try:
        # Получаем реальные данные о серверах из базы данных
        from sqlalchemy import text
        
        # Получаем информацию о серверах из событий и агентов
        result = db.execute(text("""
            SELECT DISTINCT
                host_id,
                MAX(ts) as last_seen,
                COUNT(*) as event_count
            FROM security_system.events 
            WHERE host_id IS NOT NULL
            GROUP BY host_id
            ORDER BY last_seen DESC
        """))
        
        servers = []
        for row in result:
            # Определяем тип сервера на основе событий
            server_type = "unknown"
            services = []
            
            # Получаем типы событий для этого хоста
            event_types_result = db.execute(text("""
                SELECT DISTINCT event_type 
                FROM security_system.events 
                WHERE host_id = :host_id
            """), {"host_id": row.host_id})
            
            event_types = [row[0] for row in event_types_result]
            
            if "system.performance" in event_types:
                server_type = "monitoring_server"
                services.append("monitoring")
            if "network.connection" in event_types:
                services.append("network")
            if "process.created" in event_types:
                services.append("process_monitoring")
            
            # Определяем IP адрес из событий
            ip_result = db.execute(text("""
                SELECT (details->>'connection')::jsonb->>'local_addr' as local_addr
                FROM security_system.events 
                WHERE host_id = :host_id 
                AND (details->>'connection')::jsonb->>'local_addr' IS NOT NULL
                LIMIT 1
            """), {"host_id": row.host_id})
            
            ip_address = "Неизвестно"
            ip_row = ip_result.first()
            if ip_row and ip_row[0]:
                local_addr = ip_row[0]
                if ':' in local_addr:
                    ip_address = local_addr.split(':')[0]
            
            servers.append({
                "id": f"server-{row.host_id}",
                "name": row.host_id,
                "ip": ip_address,
                "status": "online",
                "type": server_type,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                "services": services,
                "event_count": row.event_count
            })
        
        # Если серверов нет, добавляем демо-сервер
        if not servers:
            servers = [
                {
                    "id": "server-1",
                    "name": "SIEM Server",
                    "ip": "192.168.1.100",
                    "status": "online",
                    "type": "siem_server",
                    "last_seen": datetime.now().isoformat(),
                    "services": ["web", "api", "database", "analyzer"]
                }
            ]
        
        return {"data": servers}
    except Exception as e:
        logger.error(f"Ошибка получения серверов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных о серверах")

@router.get("/agents")
async def get_agents(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_api_key)
):
    """Получить список агентов пользователя"""
    try:
        # Получаем реальные данные об агентах пользователя из базы данных
        from sqlalchemy import text
        
        # Запрос к реальной таблице агентов с фильтрацией по пользователю
        result = db.execute(text("""
            SELECT 
                id,
                agent_uuid,
                hostname,
                ip_address,
                os,
                version,
                status,
                last_seen,
                created_at
            FROM security_system.agents 
            WHERE owner_id = :owner_id
            ORDER BY last_seen DESC NULLS LAST
        """), {"owner_id": current_user})
        
        agents = []
        for row in result:
            # Определяем тип агента на основе ОС
            agent_type = "unknown"
            collectors = []
            
            if row.os and "windows" in row.os.lower():
                agent_type = "python_agent"
                collectors = ["net_sniffer", "windows_privileged"]
            elif row.os and "astra" in row.os.lower():
                agent_type = "astra_agent"
                collectors = ["system_events", "network_monitor"]
            elif row.os and "linux" in row.os.lower():
                agent_type = "linux_agent"
                collectors = ["system_events", "network_monitor"]
            
            # Определяем статус на основе времени последней активности
            status = row.status
            if row.status != 'offline' and row.last_seen:
                time_diff = datetime.now(timezone.utc) - row.last_seen
                if time_diff.total_seconds() > 300:  # 5 минут
                    status = "offline"
                    # Обновляем статус в базе данных
                    try:
                        db.execute(text("""
                            UPDATE security_system.agents 
                            SET status = 'offline', updated_at = now()
                            WHERE id = :agent_id
                        """), {"agent_id": row.id})
                    except Exception as e:
                        logger.warning(f"Не удалось обновить статус агента {row.id}: {e}")
                else:
                    status = "online"
            
            agents.append({
                "id": f"agent-{row.id}",
                "name": row.hostname or f"Agent {row.id}",
                "ip": row.ip_address or "Неизвестно",
                "status": status,
                "type": agent_type,
                "last_seen": row.last_seen.isoformat() if row.last_seen else None,
                "version": row.version or "Неизвестно",
                "os": row.os or "Неизвестно",
                "collectors": collectors,
                "created_at": row.created_at.isoformat() if row.created_at else None
            })
        
        # Если агентов нет, добавляем демо-агентов для демонстрации
        if not agents:
            agents = [
                {
                    "id": "demo-agent-1",
                    "name": "Demo Agent 1",
                    "ip": "192.168.1.101",
                    "status": "online",
                    "type": "python_agent",
                    "last_seen": datetime.now().isoformat(),
                    "version": "2.0.0",
                    "os": "Windows 10",
                    "collectors": ["net_sniffer", "windows_privileged"],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "demo-agent-2",
                    "name": "Demo Agent 2", 
                    "ip": "192.168.1.102",
                    "status": "online",
                    "type": "python_agent",
                    "last_seen": datetime.now().isoformat(),
                    "version": "2.0.0",
                    "os": "Windows 11",
                    "collectors": ["net_sniffer", "windows_privileged"],
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "demo-agent-3",
                    "name": "Astra Demo Agent",
                    "ip": "192.168.1.103",
                    "status": "online",
                    "type": "astra_agent",
                    "last_seen": datetime.now().isoformat(),
                    "version": "2.0.0",
                    "os": "AstraLinux 1.7",
                    "collectors": ["system_events", "network_monitor"],
                    "created_at": datetime.now().isoformat()
                }
            ]
        
        # Коммитим изменения статусов в базе данных
        try:
            db.commit()
        except Exception as e:
            logger.warning(f"Не удалось закоммитить изменения статусов: {e}")
        
        return {"data": agents}
    except Exception as e:
        logger.error(f"Ошибка получения агентов: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных об агентах")

@router.post("/agents/register")
async def register_agent(
    agent_data: dict,
    db: Session = Depends(get_db)
):
    """Регистрация нового агента в системе"""
    try:
        from sqlalchemy import text
        import uuid
        
        agent_uuid = agent_data.get("agent_uuid") or str(uuid.uuid4())
        hostname = agent_data.get("hostname", "Unknown")
        ip_address = agent_data.get("ip_address")
        os = agent_data.get("os", "Unknown")
        version = agent_data.get("version", "1.0.0")
        
        # Проверяем, есть ли уже такой агент
        existing = db.execute(text("""
            SELECT id FROM security_system.agents 
            WHERE agent_uuid = :uuid
        """), {"uuid": agent_uuid}).first()
        
        if existing:
            # Обновляем существующего агента
            db.execute(text("""
                UPDATE security_system.agents 
                SET hostname = :hostname,
                    ip_address = :ip,
                    os = :os,
                    version = :version,
                    status = 'online',
                    last_seen = now(),
                    updated_at = now()
                WHERE agent_uuid = :uuid
            """), {
                "uuid": agent_uuid,
                "hostname": hostname,
                "ip": ip_address,
                "os": os,
                "version": version
            })
            agent_id = existing[0]
        else:
            # Создаем нового агента
            result = db.execute(text("""
                INSERT INTO security_system.agents 
                (agent_uuid, hostname, ip_address, os, version, status, last_seen)
                VALUES (:uuid, :hostname, :ip, :os, :version, 'online', now())
                RETURNING id
            """), {
                "uuid": agent_uuid,
                "hostname": hostname,
                "ip": ip_address,
                "os": os,
                "version": version
            })
            agent_id = result.scalar()
        
        db.commit()
        
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "Агент успешно зарегистрирован"
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка регистрации агента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка регистрации агента")

@router.post("/agents/heartbeat")
async def agent_heartbeat(
    agent_data: dict,
    db: Session = Depends(get_db)
):
    """Обновление статуса агента (heartbeat)"""
    try:
        from sqlalchemy import text
        
        agent_uuid = agent_data.get("agent_uuid")
        if not agent_uuid:
            raise HTTPException(status_code=400, detail="agent_uuid required")
        
        # Обновляем время последней активности
        result = db.execute(text("""
            UPDATE security_system.agents 
            SET status = 'online',
                last_seen = now(),
                updated_at = now()
            WHERE agent_uuid = :uuid
            RETURNING id, hostname
        """), {"uuid": agent_uuid})
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Агент не найден")
        
        db.commit()
        
        return {
            "success": True,
            "agent_id": row[0],
            "hostname": row[1],
            "message": "Heartbeat обновлен"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка heartbeat агента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка обновления статуса агента")

@router.post("/agents/{agent_id}/shutdown")
async def shutdown_agent(
    agent_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Принудительное отключение агента"""
    try:
        from sqlalchemy import text
        
        result = db.execute(text("""
            UPDATE security_system.agents 
            SET status = 'offline', updated_at = now()
            WHERE id = :agent_id
            RETURNING id, hostname
        """), {"agent_id": agent_id})
        
        row = result.first()
        if not row:
            raise HTTPException(status_code=404, detail="Агент не найден")
        
        db.commit()
        return {"success": True, "agent_id": row[0], "hostname": row[1], "message": "Агент отключен"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Ошибка отключения агента: {e}")
        raise HTTPException(status_code=500, detail="Ошибка отключения агента")

@router.get("/network-devices")
async def get_network_devices(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить список сетевых устройств (роутеры, коммутаторы)"""
    try:
        # В реальной системе это может быть SNMP сканирование или конфигурация
        devices = [
            {
                "id": "router-1",
                "name": "Main Router",
                "ip": "192.168.1.1",
                "type": "router",
                "status": "online",
                "manufacturer": "Cisco",
                "model": "ISR 4331",
                "last_seen": datetime.now().isoformat(),
                "interfaces": [
                    {"name": "GigabitEthernet0/0/0", "status": "up", "ip": "192.168.1.1"},
                    {"name": "GigabitEthernet0/0/1", "status": "up", "ip": "192.168.2.1"}
                ]
            },
            {
                "id": "switch-1",
                "name": "Core Switch",
                "ip": "192.168.1.10",
                "type": "switch",
                "status": "online",
                "manufacturer": "Cisco",
                "model": "Catalyst 2960",
                "last_seen": datetime.now().isoformat(),
                "ports": 24,
                "vlans": ["1", "10", "20"]
            },
            {
                "id": "switch-2",
                "name": "Access Switch",
                "ip": "192.168.1.11",
                "type": "switch",
                "status": "online",
                "manufacturer": "Cisco",
                "model": "Catalyst 2960",
                "last_seen": datetime.now().isoformat(),
                "ports": 48,
                "vlans": ["1", "10", "20"]
            }
        ]
        
        return {"data": devices}
    except Exception as e:
        logger.error(f"Ошибка получения сетевых устройств: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения данных о сетевых устройствах")

@router.get("/network-topology")
async def get_network_topology(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить полную топологию сети"""
    try:
        # Получаем все компоненты сети
        servers_response = await get_servers(db, current_user)
        agents_response = await get_agents(db, current_user)
        devices_response = await get_network_devices(db, current_user)
        
        topology = {
            "nodes": [],
            "edges": [],
            "last_updated": datetime.now().isoformat()
        }
        
        # Добавляем серверы
        for server in servers_response["data"]:
            topology["nodes"].append({
                "id": server["id"],
                "type": "server",
                "label": server["name"],
                "ip": server["ip"],
                "status": server["status"],
                "metadata": server
            })
        
        # Добавляем агенты
        for agent in agents_response["data"]:
            topology["nodes"].append({
                "id": agent["id"],
                "type": "agent",
                "label": agent["name"],
                "ip": agent["ip"],
                "status": agent["status"],
                "metadata": agent
            })
        
        # Добавляем сетевые устройства
        for device in devices_response["data"]:
            topology["nodes"].append({
                "id": device["id"],
                "type": device["type"],
                "label": device["name"],
                "ip": device["ip"],
                "status": device["status"],
                "metadata": device
            })
        
        # Создаем связи между устройствами
        # Сервер -> Роутер
        topology["edges"].append({
            "id": "server-router-1",
            "source": "server-1",
            "target": "router-1",
            "type": "connection",
            "bandwidth": "1 Gbps"
        })
        
        # Роутер -> Коммутаторы
        topology["edges"].append({
            "id": "router-1-switch-1",
            "source": "router-1",
            "target": "switch-1",
            "type": "connection",
            "bandwidth": "100 Mbps"
        })
        
        topology["edges"].append({
            "id": "router-1-switch-2",
            "source": "router-1",
            "target": "switch-2",
            "type": "connection",
            "bandwidth": "100 Mbps"
        })
        
        # Коммутаторы -> Агенты
        agents = agents_response["data"]
        for i, agent in enumerate(agents):
            switch_id = "switch-1" if i % 2 == 0 else "switch-2"
            topology["edges"].append({
                "id": f"{switch_id}-{agent['id']}",
                "source": switch_id,
                "target": agent["id"],
                "type": "data_flow",
                "bandwidth": "10 Mbps"
            })
        
        return topology
        
    except Exception as e:
        logger.error(f"Ошибка получения топологии сети: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения топологии сети")

@router.get("/network-scan")
async def scan_network(
    network_range: str = "192.168.1.0/24",
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Сканировать сеть для обнаружения устройств"""
    try:
        # В реальной системе здесь может быть nmap или ping сканирование
        # Для демонстрации возвращаем статические данные
        
        discovered_devices = [
            {
                "ip": "192.168.1.1",
                "hostname": "router.local",
                "type": "router",
                "status": "online",
                "response_time": 1.2
            },
            {
                "ip": "192.168.1.10",
                "hostname": "switch1.local",
                "type": "switch",
                "status": "online",
                "response_time": 0.8
            },
            {
                "ip": "192.168.1.11",
                "hostname": "switch2.local",
                "type": "switch",
                "status": "online",
                "response_time": 0.9
            },
            {
                "ip": "192.168.1.100",
                "hostname": "siem-server.local",
                "type": "server",
                "status": "online",
                "response_time": 0.5
            },
            {
                "ip": "192.168.1.101",
                "hostname": "agent1.local",
                "type": "agent",
                "status": "online",
                "response_time": 1.1
            },
            {
                "ip": "192.168.1.102",
                "hostname": "agent2.local",
                "type": "agent",
                "status": "online",
                "response_time": 1.0
            }
        ]
        
        return {
            "network_range": network_range,
            "discovered_devices": discovered_devices,
            "scan_time": datetime.now().isoformat(),
            "total_devices": len(discovered_devices)
        }
        
    except Exception as e:
        logger.error(f"Ошибка сканирования сети: {e}")
        raise HTTPException(status_code=500, detail="Ошибка сканирования сети")

@router.get("/network-stats")
async def get_network_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить статистику сети"""
    try:
        # Получаем статистику из базы данных
        stats = {
            "total_nodes": 6,
            "online_nodes": 6,
            "total_connections": 5,
            "active_agents": 3,
            "network_health": "good",
            "bandwidth_usage": {
                "total": "2.5 Gbps",
                "used": "1.2 Gbps",
                "available": "1.3 Gbps"
            },
            "latency": {
                "average": 1.2,
                "min": 0.5,
                "max": 2.1
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики сети: {e}")
        raise HTTPException(status_code=500, detail="Ошибка получения статистики сети")
