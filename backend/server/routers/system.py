from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.common.db import get_db
from sqlalchemy import text
from typing import Dict, Any

router = APIRouter()

@router.get("/metrics")
async def get_system_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Получить текущие системные метрики"""
    try:
        # Получаем последние метрики производительности
        result = db.execute(text("""
            SELECT details->>'performance' as performance
            FROM security_system.events
            WHERE event_type = 'system.performance'
            ORDER BY id DESC
            LIMIT 1
        """)).fetchone()
        
        if not result or not result.performance:
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "disk_percent": 0,
                "network_percent": 0
            }
        
        import json
        performance = json.loads(result.performance)
        
        return {
            "cpu_percent": round(performance.get('cpu_percent', 0), 1),
            "memory_percent": round(performance.get('memory_percent', 0), 1),
            "disk_percent": round(performance.get('disk_percent', 0), 1),
            "network_percent": round(performance.get('network_percent', 0), 1)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения метрик: {str(e)}")

@router.get("/device-info")
async def get_device_info(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Получить подробную информацию об устройстве"""
    try:
        # Получаем последние системные метрики
        metrics_result = db.execute(text("""
            SELECT details->>'performance' as performance
            FROM security_system.events
            WHERE event_type = 'system.performance'
            ORDER BY id DESC
            LIMIT 1
        """)).fetchone()
        
        metrics = {
            "cpu_percent": 0,
            "memory_percent": 0,
            "disk_percent": 0,
            "network_percent": 0,
            "memory_total_gb": 0,
            "disk_total_gb": 0
        }
        
        if metrics_result and metrics_result.performance:
            import json
            performance = json.loads(metrics_result.performance)
            metrics = {
                "cpu_percent": round(performance.get('cpu_percent', 0), 1),
                "memory_percent": round(performance.get('memory_percent', 0), 1),
                "disk_percent": round(performance.get('disk_percent', 0), 1),
                "network_percent": round(performance.get('network_percent', 0), 1),
                "memory_total_gb": round(performance.get('memory_total_gb', 0), 1),
                "disk_total_gb": round(performance.get('disk_total_gb', 0), 1)
            }
        
        return {
            "id": 1,
            "hostname": "DESKTOP-RML94J6",
            "ip": "192.168.0.23",
            "status": "online",
            "type": "python_agent",
            "last_seen": "2025-09-04T19:24:03.393866+00:00",
            "version": "1.0.0",
            "os": "Windows 10",
            "collectors": ["net_sniffer", "windows_privileged"],
            "metrics": metrics
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации об устройстве: {str(e)}")
