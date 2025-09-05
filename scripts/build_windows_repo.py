#!/usr/bin/env python3
"""
Скрипт для создания Windows офлайн репозитория с зависимостями
"""

import os
import shutil
import subprocess
import json
import zipfile
from pathlib import Path
import platform

def download_python_packages():
    """Скачивание Python пакетов для Windows"""
    print("Downloading Python packages for Windows...")
    
    packages_dir = Path("offline_repos/windows/siem-windows-agent-v2.0.0/dependencies/packages")
    packages_dir.mkdir(parents=True, exist_ok=True)
    
    # Список пакетов из requirements.txt
    packages = [
        "requests>=2.31.0",
        "PyYAML>=6.0",
        "scapy>=2.5.0", 
        "psutil>=5.9.0",
        "wmi>=1.5.1",
        "pywin32>=311"
    ]
    
    # Скачивание пакетов
    for package in packages:
        print(f"Downloading {package}...")
        try:
            subprocess.run([
                "pip", "download", 
                "--platform", "win_amd64",
                "--python-version", "312",
                "--only-binary=:all:",
                "--dest", str(packages_dir),
                package
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to download {package}: {e}")
            # Попробуем без платформы
            try:
                subprocess.run([
                    "pip", "download", 
                    "--dest", str(packages_dir),
                    package
                ], check=True)
            except subprocess.CalledProcessError:
                print(f"Error: Could not download {package}")

def create_windows_agent():
    """Создание Windows агента"""
    print("Creating Windows agent...")
    
    base_dir = Path("offline_repos/windows/siem-windows-agent-v2.0.0")
    
    # Создание структуры
    dirs = [
        "agent", "dependencies/packages", "install", 
        "config", "service", "docs", "logs"
    ]
    
    for dir_path in dirs:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Копирование агента
    if Path("agents/python").exists():
        shutil.copytree("agents/python", base_dir / "agent", dirs_exist_ok=True)
    else:
        print("Warning: agents/python directory not found")
    
    # Создание install.bat
    install_script = '''@echo off
echo Installing SIEM Windows Agent v2.0.0...

REM Проверка прав администратора
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges
) else (
    echo This script requires administrator privileges
    echo Please run as administrator
    pause
    exit /b 1
)

REM Создание директории
if not exist "C:\\SIEM-Agent" mkdir "C:\\SIEM-Agent"
cd /d "C:\\SIEM-Agent"

REM Копирование файлов
xcopy /E /I /Y "%~dp0..\\agent" "C:\\SIEM-Agent\\agent"
xcopy /E /I /Y "%~dp0..\\config" "C:\\SIEM-Agent\\config"

REM Проверка Python
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo Python found
) else (
    echo Python not found. Please install Python 3.8+ from https://python.org
    echo Then run this script again
    pause
    exit /b 1
)

REM Установка зависимостей
echo Installing Python packages...
cd "C:\\SIEM-Agent\\agent"
pip install --no-index --find-links "%~dp0..\\dependencies\\packages" -r requirements.txt

REM Создание конфигурации
if not exist "C:\\SIEM-Agent\\config\\agent.yaml" (
    copy "C:\\SIEM-Agent\\config\\agent.example.yaml" "C:\\SIEM-Agent\\config\\agent.yaml"
    echo.
    echo IMPORTANT: Please edit C:\\SIEM-Agent\\config\\agent.yaml
    echo Set your SIEM server URL and API key
    echo.
)

REM Установка службы
echo Installing Windows service...
sc create "SIEMAgent" binPath= "python C:\\SIEM-Agent\\agent\\windows_agent.py" start= auto
sc description "SIEMAgent" "SIEM Security Information and Event Management Agent"

echo Installation completed!
echo Please configure the agent in C:\\SIEM-Agent\\config\\agent.yaml
echo Then start the service: sc start SIEMAgent
pause
'''
    
    with open(base_dir / "install" / "install.bat", "w", encoding="utf-8") as f:
        f.write(install_script)
    
    # Создание конфигурации
    config_example = '''server:
  url: "http://your-siem-server:8000"
  api_key: "your-api-key-here"

agent:
  hostname: "{{HOSTNAME}}"
  collect_interval: 30
  log_level: "INFO"
  data_retention_days: 7

collectors:
  system_metrics:
    enabled: true
    interval: 30
  network_connections:
    enabled: true
    interval: 60
  processes:
    enabled: true
    interval: 120
  windows_events:
    enabled: true
    interval: 300
    log_types: ["Security", "System", "Application"]

logging:
  level: "INFO"
  file: "C:\\\\SIEM-Agent\\\\logs\\\\agent.log"
  max_size_mb: 10
  backup_count: 5
'''
    
    with open(base_dir / "config" / "agent.example.yaml", "w", encoding="utf-8") as f:
        f.write(config_example)
    
    # Создание README
    readme = '''# SIEM Windows Agent v2.0.0 - Офлайн Репозиторий

## Описание
Офлайн репозиторий для развертывания SIEM агента на Windows системах без доступа к интернету.

## Содержимое
- `agent/` - Исходный код агента
- `dependencies/` - Python пакеты
- `install/` - Скрипты установки
- `config/` - Конфигурационные файлы

## Требования
- Windows 10/11 или Windows Server 2016+
- Python 3.8+ (установите с https://python.org)
- Права администратора для установки

## Установка

### Автоматическая установка
1. Распакуйте архив в любую папку
2. Запустите `install\\install.bat` от имени администратора
3. Настройте конфигурацию в `C:\\SIEM-Agent\\config\\agent.yaml`
4. Запустите службу: `sc start SIEMAgent`

### Ручная установка
1. Установите Python 3.8+ с https://python.org
2. Скопируйте папку agent в C:\\SIEM-Agent\\
3. Установите зависимости: `pip install -r requirements.txt`
4. Настройте конфигурацию
5. Запустите агента: `python windows_agent.py`

## Конфигурация
Отредактируйте файл `C:\\SIEM-Agent\\config\\agent.yaml`:
```yaml
server:
  url: "http://your-siem-server:8000"
  api_key: "your-api-key"

agent:
  hostname: "your-computer-name"
  collect_interval: 30
  log_level: "INFO"
```

## Управление службой
- Запуск: `sc start SIEMAgent`
- Остановка: `sc stop SIEMAgent`
- Удаление: `sc delete SIEMAgent`

## Поддерживаемые функции
- Сбор системных метрик (CPU, память, диск, сеть)
- Мониторинг процессов
- Сбор сетевых подключений
- Windows Event Log
- WMI данные

## Лицензия
Proprietary - SIEM Security System
'''
    
    with open(base_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    # Создание манифеста
    manifest = {
        "name": "SIEM Windows Agent",
        "version": "2.0.0",
        "platform": "windows",
        "python_version": "3.8+",
        "dependencies": [
            "requests>=2.31.0",
            "PyYAML>=6.0",
            "scapy>=2.5.0",
            "psutil>=5.9.0",
            "wmi>=1.5.1",
            "pywin32>=311"
        ],
        "install_script": "install/install.bat",
        "config_file": "config/agent.yaml",
        "service_name": "SIEMAgent"
    }
    
    with open(base_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def create_zip_archive():
    """Создание ZIP архива"""
    print("Creating ZIP archive...")
    
    base_dir = Path("offline_repos/windows/siem-windows-agent-v2.0.0")
    archive_path = "offline_repos/windows/siem-windows-agent-v2.0.0.zip"
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(base_dir.parent)
                zipf.write(file_path, arcname)
    
    print(f"Archive created: {archive_path}")

def main():
    """Основная функция"""
    print("Building Windows offline repository...")
    
    # Создание базовой структуры
    create_windows_agent()
    
    # Скачивание зависимостей
    download_python_packages()
    
    # Создание архива
    create_zip_archive()
    
    print("Windows repository build completed!")

if __name__ == "__main__":
    main()
