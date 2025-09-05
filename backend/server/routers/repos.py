"""
Роутер для управления офлайн репозиториями агентов
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse

router = APIRouter()

# Путь к репозиториям
REPOS_BASE_PATH = Path("/app/offline_repos")

@router.get("/list")
async def list_repositories() -> List[Dict[str, Any]]:
    """Получить список доступных репозиториев"""
    try:
        repositories = []
        
        # Проверяем Windows репозиторий
        windows_zip = REPOS_BASE_PATH / "windows" / "siem-windows-agent-v2.0.0.zip"
        if windows_zip.exists():
            stat = windows_zip.stat()
            repositories.append({
                "id": "windows-agent-v2",
                "name": "SIEM Windows Agent v2.0.0",
                "platform": "Windows 10/11, Windows Server",
                "version": "2.0.0",
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 1),
                "download_url": "/api/repos/download/windows/siem-windows-agent-v2.0.0.zip",
                "description": "Офлайн агент для Windows с полной поддержкой зависимостей",
                "features": [
                    "Полностью офлайн - все зависимости включены",
                    "Установка как служба Windows",
                    "Мониторинг событий безопасности и WMI",
                    "Мониторинг процессов и сетевых соединений",
                    "Heartbeat мониторинг",
                    "Автоматический запуск при загрузке системы"
                ],
                "requirements": [
                    "Windows 10/11 или Windows Server 2016+",
                    "Python 3.8+ (включен в архив)",
                    "Права администратора",
                    "Сетевое подключение к SIEM серверу"
                ]
            })
        
        # Проверяем Astra Linux репозиторий
        astra_zip = REPOS_BASE_PATH / "astra" / "siem-astra-agent-v2.0.0.zip"
        if astra_zip.exists():
            stat = astra_zip.stat()
            repositories.append({
                "id": "astra-agent-v2",
                "name": "SIEM Astra Linux Agent v2.0.0",
                "platform": "Astra Linux 1.7+",
                "version": "2.0.0",
                "size_bytes": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 1),
                "download_url": "/api/repos/download/astra/siem-astra-agent-v2.0.0.zip",
                "description": "Офлайн агент для Astra Linux с полной поддержкой зависимостей",
                "features": [
                    "Полностью офлайн - все зависимости включены",
                    "Установка как systemd служба",
                    "Мониторинг системных событий и процессов",
                    "Сбор данных аутентификации и сетевых соединений",
                    "Heartbeat мониторинг",
                    "Автоматический запуск при загрузке системы"
                ],
                "requirements": [
                    "Astra Linux 1.7 или выше",
                    "Root права для установки",
                    "Сетевое подключение к SIEM серверу"
                ]
            })
        
        return repositories
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка репозиториев: {str(e)}")

@router.get("/download/{platform}/{filename}")
async def download_repository(platform: str, filename: str):
    """Скачать репозиторий агента"""
    try:
        file_path = REPOS_BASE_PATH / platform / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Репозиторий не найден")
        
        if not file_path.is_file():
            raise HTTPException(status_code=400, detail="Указанный путь не является файлом")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Expose-Headers': 'Content-Disposition'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка скачивания репозитория: {str(e)}")

@router.post("/build")
async def build_repositories(background_tasks: BackgroundTasks):
    """Запустить сборку всех репозиториев в фоновом режиме"""
    try:
        # Запускаем сборку в фоновом режиме
        background_tasks.add_task(build_all_repositories)
        
        return {
            "message": "Сборка репозиториев запущена в фоновом режиме",
            "status": "started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска сборки: {str(e)}")

@router.get("/build/status")
async def get_build_status():
    """Получить статус сборки репозиториев"""
    try:
        # Проверяем наличие файлов статуса
        status_file = REPOS_BASE_PATH / "build_status.json"
        
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)
            return status
        else:
            return {
                "status": "not_started",
                "message": "Сборка не запускалась"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения статуса сборки: {str(e)}")

async def build_all_repositories():
    """Функция сборки всех репозиториев (запускается в фоне)"""
    try:
        # Создаем файл статуса
        status_file = REPOS_BASE_PATH / "build_status.json"
        
        # Обновляем статус - начали
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "building",
                "message": "Сборка репозиториев в процессе...",
                "progress": 0
            }, f, ensure_ascii=False, indent=2)
        
        # Запускаем сборку Windows репозитория
        try:
            subprocess.run([
                "python", "scripts/build_windows_repo.py"
            ], cwd="/app", check=True)
            
            # Обновляем прогресс
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "status": "building",
                    "message": "Windows репозиторий собран, собираем Astra Linux...",
                    "progress": 50
                }, f, ensure_ascii=False, indent=2)
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка сборки Windows репозитория: {e}")
        
        # Запускаем сборку Astra Linux репозитория
        try:
            subprocess.run([
                "python", "scripts/build_astra_repo.py"
            ], cwd="/app", check=True)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Ошибка сборки Astra Linux репозитория: {e}")
        
        # Обновляем статус - завершено
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "completed",
                "message": "Все репозитории успешно собраны",
                "progress": 100,
                "repositories": [
                    "siem-windows-agent-v2.0.0.zip",
                    "siem-astra-agent-v2.0.0.zip"
                ]
            }, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        # Обновляем статус - ошибка
        with open(status_file, 'w', encoding='utf-8') as f:
            json.dump({
                "status": "error",
                "message": f"Ошибка сборки: {str(e)}",
                "progress": 0
            }, f, ensure_ascii=False, indent=2)

@router.get("/info/{platform}/{filename}")
async def get_repository_info(platform: str, filename: str):
    """Получить информацию о репозитории"""
    try:
        # Ищем manifest.json в распакованном репозитории
        manifest_path = REPOS_BASE_PATH / platform / filename.replace('.zip', '') / "manifest.json"
        
        if manifest_path.exists():
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            return manifest
        else:
            # Если manifest нет, возвращаем базовую информацию
            file_path = REPOS_BASE_PATH / platform / filename
            if file_path.exists():
                stat = file_path.stat()
                return {
                    "name": filename.replace('.zip', ''),
                    "platform": platform,
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 1)
                }
            else:
                raise HTTPException(status_code=404, detail="Репозиторий не найден")
                
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о репозитории: {str(e)}")
