from fastapi import APIRouter, Query, HTTPException, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import random
import json
from sqlalchemy.orm import Session
from backend.common.db import get_session

router = APIRouter(prefix="/traffic", tags=["traffic"])

# Реальный сбор пакетов через агентов
def get_real_packets_from_agents() -> List[Dict[str, Any]]:
    """Получает реальные пакеты от агентов"""
    try:
        # Здесь будет реальная логика получения пакетов от агентов
        # Пока что возвращаем пустой список
        return []
    except Exception as e:
        logger.error(f"Error getting packets from agents: {e}")
        return []

@router.get("/packets")
async def get_packets(
    limit: int = Query(100, ge=1, le=1000, description="Количество пакетов"),
    protocol: Optional[str] = Query(None, description="Фильтр по протоколу"),
    src_ip: Optional[str] = Query(None, description="Фильтр по IP источника"),
    dst_ip: Optional[str] = Query(None, description="Фильтр по IP назначения"),
    port: Optional[int] = Query(None, description="Фильтр по порту")
):
    """
    Получить список пакетов сетевого трафика из реальных данных
    """
    try:
        with get_session() as db:
            from sqlalchemy import text
            
            # Получаем сетевые события из базы данных
            query = """
                SELECT 
                    id,
                    ts,
                    event_type,
                    severity,
                    details,
                    host_id
                FROM security_system.events 
                WHERE event_type = 'network.connection'
                ORDER BY ts DESC
                LIMIT :limit
            """
            
            result = db.execute(text(query), {"limit": limit})
            packets = []
            
            for row in result:
                details = row.details or {}
                connection = details.get('connection', {})
                
                # Извлекаем IP адреса и порты
                local_addr = connection.get('local_addr', '')
                remote_addr = connection.get('remote_addr', '')
                
                if ':' in local_addr:
                    src_ip_addr, src_port = local_addr.rsplit(':', 1)
                    src_port = int(src_port) if src_port.isdigit() else None
                else:
                    src_ip_addr = local_addr
                    src_port = None
                
                if ':' in remote_addr:
                    dst_ip_addr, dst_port = remote_addr.rsplit(':', 1)
                    dst_port = int(dst_port) if dst_port.isdigit() else None
                else:
                    dst_ip_addr = remote_addr
                    dst_port = None
                
                # Определяем протокол на основе портов
                protocol_name = "TCP"  # По умолчанию
                if dst_port:
                    if dst_port in [80, 8080]:
                        protocol_name = "HTTP"
                    elif dst_port in [443, 8443]:
                        protocol_name = "HTTPS"
                    elif dst_port == 53:
                        protocol_name = "DNS"
                    elif dst_port == 22:
                        protocol_name = "SSH"
                    elif dst_port == 21:
                        protocol_name = "FTP"
                    elif dst_port == 25:
                        protocol_name = "SMTP"
                    elif dst_port == 3389:
                        protocol_name = "RDP"
                
                # Применяем фильтры
                if protocol and protocol_name.lower() != protocol.lower():
                    continue
                if src_ip and src_ip not in src_ip_addr:
                    continue
                if dst_ip and dst_ip not in dst_ip_addr:
                    continue
                if port and port not in [src_port, dst_port]:
                    continue
                
                # Определяем severity на основе типа соединения
                severity = "info"
                if connection.get('status') == 'ESTABLISHED':
                    severity = "success"
                elif connection.get('status') == 'LISTENING':
                    severity = "warning"
                
                packet = {
                    "id": row.id,
                    "timestamp": row.ts.isoformat() if row.ts else datetime.now().isoformat(),
                    "src_ip": src_ip_addr,
                    "dst_ip": dst_ip_addr,
                    "src_port": src_port,
                    "dst_port": dst_port,
                    "protocol": protocol_name,
                    "length": 0,  # Размер пакета не сохраняется
                    "info": f"{connection.get('status', 'UNKNOWN')} {protocol_name} connection",
                    "flags": [connection.get('status', 'UNKNOWN')] if connection.get('status') else None,
                    "payload_preview": f"{protocol_name} data...",
                    "severity": severity,
                    "host_id": row.host_id
                }
                
                packets.append(packet)
        
        return {
            "packets": packets,
            "total": len(packets),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения пакетов: {str(e)}")

@router.get("/stats")
async def get_traffic_stats():
    """Получить статистику трафика из реальных данных"""
    try:
        with get_session() as db:
            from sqlalchemy import text
            
            # Получаем статистику сетевых событий
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_connections,
                    COUNT(CASE WHEN (details->>'connection')::jsonb->>'status' = 'ESTABLISHED' THEN 1 END) as established_connections,
                    COUNT(CASE WHEN (details->>'connection')::jsonb->>'status' = 'LISTENING' THEN 1 END) as listening_connections
                FROM security_system.events 
                WHERE event_type = 'network.connection'
            """))
            
            row = result.first()
            total_connections = row[0] if row else 0
            established_connections = row[1] if row else 0
            listening_connections = row[2] if row else 0
            
            # Получаем статистику по протоколам
            protocol_result = db.execute(text("""
                SELECT 
                    'TCP' as protocol,
                    COUNT(*) as count
                FROM security_system.events 
                WHERE event_type = 'network.connection'
                AND (details->>'connection')::jsonb->>'remote_addr' IS NOT NULL
            """))
            
            protocol_stats = {}
            for row in protocol_result:
                protocol_stats[row[0]] = row[1]
            
            # Получаем статистику трафика из системных метрик
            traffic_result = db.execute(text("""
                SELECT 
                    SUM(((details->>'performance')::jsonb->>'network_sent_mb')::numeric) as total_sent_mb,
                    SUM(((details->>'performance')::jsonb->>'network_recv_mb')::numeric) as total_recv_mb
                FROM security_system.events 
                WHERE event_type = 'system.performance'
                AND (details->>'performance')::jsonb->>'network_sent_mb' IS NOT NULL
            """))
            
            traffic_row = traffic_result.first()
            total_sent_mb = float(traffic_row[0]) if traffic_row and traffic_row[0] else 0
            total_recv_mb = float(traffic_row[1]) if traffic_row and traffic_row[1] else 0
            total_bytes = (total_sent_mb + total_recv_mb) * 1024 * 1024
            
            stats = {
                "total_packets": total_connections,
                "tcp_packets": protocol_stats.get('TCP', 0),
                "udp_packets": 0,  # UDP не отслеживается в текущей реализации
                "http_packets": protocol_stats.get('HTTP', 0),
                "https_packets": protocol_stats.get('HTTPS', 0),
                "dns_packets": protocol_stats.get('DNS', 0),
                "icmp_packets": 0,  # ICMP не отслеживается
                "bytes_total": int(total_bytes),
                "packets_per_second": total_connections // 60 if total_connections > 0 else 0,  # Примерная оценка
                "threats_detected": 0,  # Пока не реализовано
                "established_connections": established_connections,
                "listening_connections": listening_connections,
                "last_updated": datetime.now().isoformat()
            }
            
            return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статистики: {str(e)}")

@router.get("/protocols")
async def get_protocol_distribution():
    """Получить распределение по протоколам из реальных данных"""
    try:
        with get_session() as db:
            from sqlalchemy import text
            
            # Получаем распределение по протоколам
            result = db.execute(text("""
                SELECT 
                    'TCP' as protocol,
                    COUNT(*) as count
                FROM security_system.events 
                WHERE event_type = 'network.connection'
                AND (details->>'connection')::jsonb->>'remote_addr' IS NOT NULL
                GROUP BY protocol
                ORDER BY count DESC
            """))
            
            protocols = {}
            total_connections = 0
            
            for row in result:
                protocols[row[0]] = row[1]
                total_connections += row[1]
            
            # Конвертируем в проценты
            if total_connections > 0:
                for protocol in protocols:
                    protocols[protocol] = round((protocols[protocol] / total_connections) * 100, 1)
            
            return {
                "protocols": protocols,
                "total_connections": total_connections,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения распределения протоколов: {str(e)}")

@router.post("/capture/start")
async def start_capture():
    """Начать захват пакетов"""
    try:
        # В реальной системе здесь будет запуск процесса захвата
        # Например, через subprocess или интеграцию с tcpdump/tshark
        return {
            "status": "started",
            "message": "Захват пакетов запущен",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска захвата: {str(e)}")

@router.post("/capture/stop")
async def stop_capture():
    """Остановить захват пакетов"""
    try:
        # В реальной системе здесь будет остановка процесса захвата
        return {
            "status": "stopped",
            "message": "Захват пакетов остановлен",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка остановки захвата: {str(e)}")

@router.get("/packet/{packet_id}")
async def get_packet_details(packet_id: int):
    """Получить детальную информацию о пакете"""
    try:
        # В реальной системе здесь будет поиск пакета в БД или кэше
        # Пока что возвращаем базовую информацию
        packet = {
            "id": packet_id,
            "timestamp": datetime.now().isoformat(),
            "src_ip": "unknown",
            "dst_ip": "unknown",
            "src_port": 0,
            "dst_port": 0,
            "protocol": "unknown",
            "length": 0,
            "info": "Packet details not available",
            "severity": "info"
        }
        
        return packet
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения деталей пакета: {str(e)}")
