"""
API роутер для управления анализатором SIEM
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

from ...analyzer.integration import (
    get_analyzer_integration, 
    initialize_analyzer_integration,
    shutdown_analyzer_integration
)
from ...analyzer.config import AnalyzerConfig, create_analyzer_config
from ...analyzer.engine.rule import Rule, RuleSet
from ...common.db import get_session

router = APIRouter()
logger = logging.getLogger("analyzer.router")


@router.get("/status")
async def get_analyzer_status():
    """Получить статус анализатора"""
    try:
        integration = await get_analyzer_integration()
        return integration.get_integration_status()
    except Exception as e:
        logger.error(f"Error getting analyzer status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analyzer status: {str(e)}")


@router.post("/start")
async def start_analyzer(background_tasks: BackgroundTasks):
    """Запустить анализатор"""
    try:
        integration = await get_analyzer_integration()
        
        if integration.is_integrated:
            return {"message": "Analyzer is already running", "status": "running"}
        
        # Запустить в фоновом режиме
        background_tasks.add_task(integration.integrate)
        
        return {"message": "Analyzer starting...", "status": "starting"}
        
    except Exception as e:
        logger.error(f"Error starting analyzer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start analyzer: {str(e)}")


@router.post("/stop")
async def stop_analyzer():
    """Остановить анализатор"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            return {"message": "Analyzer is not running", "status": "stopped"}
        
        await integration.disintegrate()
        
        return {"message": "Analyzer stopped successfully", "status": "stopped"}
        
    except Exception as e:
        logger.error(f"Error stopping analyzer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop analyzer: {str(e)}")


@router.post("/restart")
async def restart_analyzer(background_tasks: BackgroundTasks):
    """Перезапустить анализатор"""
    try:
        integration = await get_analyzer_integration()
        
        # Остановить, если запущен
        if integration.is_integrated:
            await integration.disintegrate()
        
        # Запустить заново
        background_tasks.add_task(integration.integrate)
        
        return {"message": "Analyzer restarting...", "status": "restarting"}
        
    except Exception as e:
        logger.error(f"Error restarting analyzer: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart analyzer: {str(e)}")


@router.get("/health")
async def health_check():
    """Проверить состояние анализатора"""
    try:
        integration = await get_analyzer_integration()
        return await integration.health_check()
    except Exception as e:
        logger.error(f"Error during health check: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/config")
async def get_analyzer_config():
    """Получить текущую конфигурацию анализатора"""
    try:
        integration = await get_analyzer_integration()
        return integration.config.to_dict()
    except Exception as e:
        logger.error(f"Error getting analyzer config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")


@router.put("/config")
async def update_analyzer_config(config_data: Dict[str, Any]):
    """Обновить конфигурацию анализатора"""
    try:
        # Создать новую конфигурацию
        new_config = create_analyzer_config(**config_data)
        
        # Получить интеграцию и обновить конфигурацию
        integration = await get_analyzer_integration()
        await integration.reload_config(new_config)
        
        return {"message": "Configuration updated successfully", "config": new_config.to_dict()}
        
    except Exception as e:
        logger.error(f"Error updating analyzer config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.get("/rules")
async def get_analyzer_rules():
    """Получить список загруженных правил"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Получить правила из движка
        rule_engine = integration.analyzer_core.rule_engine
        rules = rule_engine.rule_set.rules
        
        return {
            "total_rules": len(rules),
            "rules": [rule.to_dict() for rule in rules]
        }
        
    except Exception as e:
        logger.error(f"Error getting analyzer rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rules: {str(e)}")


@router.get("/rules/{rule_name}")
async def get_rule_details(rule_name: str):
    """Получить детали конкретного правила"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Получить правило по имени
        rule_engine = integration.analyzer_core.rule_engine
        rule = rule_engine.get_rule(rule_name)
        
        if not rule:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")
        
        return rule.to_dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting rule details: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get rule details: {str(e)}")


@router.post("/rules/reload")
async def reload_rules():
    """Перезагрузить правила анализатора"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Перезагрузить правила
        await integration.analyzer_core._load_rules()
        
        return {"message": "Rules reloaded successfully"}
        
    except Exception as e:
        logger.error(f"Error reloading rules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to reload rules: {str(e)}")


@router.post("/events/process")
async def process_event(event: Dict[str, Any]):
    """Обработать одно событие через анализатор"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Обработать событие
        results = await integration.process_event(event)
        
        return {
            "event_processed": True,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process event: {str(e)}")


@router.post("/events/process-batch")
async def process_events_batch(events: List[Dict[str, Any]]):
    """Обработать пакет событий через анализатор"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Обработать события
        results = await integration.process_events_batch(events)
        
        return {
            "events_processed": len(events),
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error processing events batch: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process events batch: {str(e)}")


@router.get("/stats")
async def get_analyzer_stats():
    """Получить статистику работы анализатора"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Получить статистику из движка
        analyzer_status = integration.analyzer_core.get_status()
        
        return {
            "analyzer_stats": analyzer_status,
            "integration_stats": {
                "is_integrated": integration.is_integrated,
                "uptime_seconds": (integration.integration_start_time - datetime.utcnow()).total_seconds() if integration.integration_start_time else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting analyzer stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/test")
async def test_analyzer():
    """Протестировать работу анализатора"""
    try:
        integration = await get_analyzer_integration()
        
        if not integration.is_integrated:
            raise HTTPException(status_code=400, detail="Analyzer is not running")
        
        # Создать тестовое событие
        test_event = {
            "event_type": "test.analyzer",
            "src_ip": "127.0.0.1",
            "dst_ip": "127.0.0.1",
            "timestamp": datetime.utcnow().isoformat(),
            "host_id": "test-host",
            "details": {
                "test": True,
                "message": "Test event for analyzer"
            }
        }
        
        # Обработать тестовое событие
        results = await integration.process_event(test_event)
        
        return {
            "test_completed": True,
            "test_event": test_event,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error testing analyzer: {e}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.delete("/shutdown")
async def shutdown_analyzer():
    """Полностью остановить анализатор"""
    try:
        await shutdown_analyzer_integration()
        
        return {"message": "Analyzer shutdown completed"}
        
    except Exception as e:
        logger.error(f"Error shutting down analyzer: {e}")
        raise HTTPException(status_code=500, detail=f"Shutdown failed: {str(e)}")
