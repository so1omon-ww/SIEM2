import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .settings import settings
from fastapi.staticfiles import StaticFiles
from .routers import auth, events, alerts, analyzer, traffic, network, dashboard, system, repos, alert_actions

log = logging.getLogger("security-system.app")
app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://192.168.0.23:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.0.23:8000",
        "http://localhost:8000",
        "http://127.0.0.1:8000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(events.router, prefix="/api/events", tags=["events"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["alerts"])
app.include_router(analyzer.router, prefix="/api/analyzer", tags=["analyzer"])
app.include_router(traffic.router, prefix="/api", tags=["traffic"])
app.include_router(network.router, prefix="/api/network", tags=["network"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(system.router, prefix="/api/system", tags=["system"])
app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
app.include_router(alert_actions.router, prefix="/api/alert-actions", tags=["alert-actions"])

# Статическая раздача офлайн-репозиториев (артефактов) для установки агентов
# Файлы должны лежать внутри контейнера по пути /app/offline_repos
try:
    from fastapi.responses import FileResponse
    import os
    
    @app.get("/files/{file_path:path}")
    async def download_file(file_path: str):
        """Скачивание файлов агентов с правильными заголовками"""
        full_path = f"/app/offline_repos/{file_path}"
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(
                path=full_path,
                filename=os.path.basename(full_path),
                media_type='application/octet-stream',
                headers={
                    'Content-Disposition': f'attachment; filename="{os.path.basename(full_path)}"',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Expose-Headers': 'Content-Disposition'
                }
            )
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="File not found")
    
    @app.get("/repos/{file_path:path}")
    async def download_repo_file(file_path: str):
        """Скачивание файлов агентов через /repos эндпоинт (для совместимости с Nginx)"""
        full_path = f"/app/offline_repos/{file_path}"
        if os.path.exists(full_path) and os.path.isfile(full_path):
            return FileResponse(
                path=full_path,
                filename=os.path.basename(full_path),
                media_type='application/octet-stream',
                headers={
                    'Content-Disposition': f'attachment; filename="{os.path.basename(full_path)}"',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                    'Access-Control-Expose-Headers': 'Content-Disposition'
                }
            )
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="File not found")
    
    log.info("Mounted download endpoint at /files")
except Exception as e:
    log.warning(f"Couldn't mount /files download endpoint: {e}")
    # Fallback to static files
    try:
        app.mount("/files", StaticFiles(directory="/app/offline_repos"), name="files")
        log.info("Mounted static files at /files")
    except Exception as e2:
        log.warning(f"Couldn't mount /files static files: {e2}")

@app.on_event("startup")
async def startup_event():
    """Событие запуска приложения"""
    log.info("Starting SIEM Security System...")
    
    # Инициализация анализатора
    try:
        from ..analyzer.integration import initialize_analyzer_integration
        await initialize_analyzer_integration()
        log.info("Analyzer integration initialized successfully")
    except ImportError as e:
        log.error(f"Failed to import analyzer integration: {e}")
    except Exception as e:
        log.error(f"Failed to initialize analyzer integration: {e}")
        # Не останавливаем приложение, если анализатор не инициализировался

@app.on_event("shutdown")
async def shutdown_event():
    """Событие остановки приложения"""
    log.info("Shutting down SIEM Security System...")
    
    # Остановить интеграцию анализатора
    try:
        from ..analyzer.integration import shutdown_analyzer_integration
        await shutdown_analyzer_integration()
        log.info("Analyzer integration shutdown completed")
    except ImportError as e:
        log.error(f"Failed to import analyzer integration for shutdown: {e}")
    except Exception as e:
        log.error(f"Failed to shutdown analyzer integration: {e}")

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "SIEM Security System API",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Проверка состояния системы"""
    return {
        "status": "healthy",
        "service": "SIEM Security System",
        "version": "2.0.0"
    }
