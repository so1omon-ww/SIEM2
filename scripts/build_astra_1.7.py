#!/usr/bin/env python3
"""
Специальный скрипт для создания Astra Linux 1.7 репозитория
"""

import os
import shutil
import subprocess
import json
import zipfile
from pathlib import Path

def download_python_packages_astra_1_7():
    """Скачивание Python пакетов для Astra Linux 1.7"""
    print("Downloading Python packages for Astra Linux 1.7...")
    
    packages_dir = Path("offline_repos/astra/siem-astra-agent-v2.0.0")
    packages_dir.mkdir(parents=True, exist_ok=True)
    
    # Список пакетов, совместимых с Python 3.7
    packages = [
        "requests>=2.25.0,<3.0.0",
        "PyYAML>=5.4.0,<6.0.0", 
        "psutil>=5.8.0,<6.0.0",
        "scapy>=2.4.0,<3.0.0"
    ]
    
    # Скачивание пакетов для Python 3.7
    for package in packages:
        print(f"Downloading {package}...")
        try:
            subprocess.run([
                "pip", "download", 
                "--python-version", "37",
                "--platform", "linux_x86_64",
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

def create_astra_agent_1_7():
    """Создание Astra Linux 1.7 агента"""
    print("Creating Astra Linux 1.7 agent...")
    
    base_dir = Path("offline_repos/astra/siem-astra-agent-v2.0.0")
    
    # Создание структуры
    dirs = [
        "agent", "packages", "install",
        "config", "service", "docs", "logs"
    ]
    
    for dir_path in dirs:
        (base_dir / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Копирование агента
    if Path("agents/python").exists():
        shutil.copytree("agents/python", base_dir / "agent", dirs_exist_ok=True)
    else:
        print("Warning: agents/python directory not found")
    
    # Создание специального requirements.txt для Astra Linux 1.7
    requirements_astra = '''# Requirements for Astra Linux 1.7 (Python 3.7)
requests>=2.25.0,<3.0.0
PyYAML>=5.4.0,<6.0.0
psutil>=5.8.0,<6.0.0
scapy>=2.4.0,<3.0.0
'''
    
    with open(base_dir / "agent" / "requirements_astra_1.7.txt", "w") as f:
        f.write(requirements_astra)
    
    # Создание install.sh для Astra Linux 1.7
    install_script = '''#!/bin/bash
set -e

echo "Installing SIEM Astra Linux Agent v2.0.0 for Astra Linux 1.7..."

# Проверка root прав
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (use sudo)"
    exit 1
fi

# Проверка версии Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Detected Python version: $PYTHON_VERSION"

if [[ "$PYTHON_VERSION" < "3.7" ]]; then
    echo "Error: Python 3.7+ required, found $PYTHON_VERSION"
    echo "Please upgrade Python or use a different installation method"
    exit 1
fi

# Создание пользователя для агента
if ! id "siem-agent" &>/dev/null; then
    useradd -r -s /bin/false -d /opt/siem-agent siem-agent
fi

# Создание директорий
mkdir -p /opt/siem-agent/{agent,config,logs}
mkdir -p /var/log/siem-agent

# Копирование файлов
cp -r agent/* /opt/siem-agent/agent/
cp -r config/* /opt/siem-agent/config/
cp service/siem-agent.service /etc/systemd/system/

# Установка системных пакетов
echo "Installing system packages..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y python3-pip python3-setuptools python3-wheel
elif command -v yum &> /dev/null; then
    yum install -y python3-pip python3-setuptools python3-wheel
elif command -v dnf &> /dev/null; then
    dnf install -y python3-pip python3-setuptools python3-wheel
else
    echo "Warning: Package manager not found. Please install Python packages manually."
fi

# Установка Python зависимостей
echo "Installing Python packages..."
cd /opt/siem-agent/agent

# Используем специальный requirements для Astra Linux 1.7
if [ -f "requirements_astra_1.7.txt" ]; then
    echo "Using Astra Linux 1.7 specific requirements..."
    if [ -d "../packages" ] && [ "$(ls -A ../packages)" ]; then
        pip3 install --no-index --find-links ../packages -r requirements_astra_1.7.txt
    else
        pip3 install -r requirements_astra_1.7.txt
    fi
else
    echo "Using standard requirements..."
    if [ -d "../packages" ] && [ "$(ls -A ../packages)" ]; then
        pip3 install --no-index --find-links ../packages -r requirements.txt
    else
        pip3 install -r requirements.txt
    fi
fi

# Настройка прав
chown -R siem-agent:siem-agent /opt/siem-agent
chmod +x /opt/siem-agent/agent/windows_agent.py

# Включение и запуск службы
systemctl daemon-reload
systemctl enable siem-agent
systemctl start siem-agent

echo "Installation completed!"
echo "Please configure the agent in /opt/siem-agent/config/agent.yaml"
echo "Agent is compatible with Astra Linux 1.7 (Python 3.7+)"
'''
    
    with open(base_dir / "install" / "install.sh", "w") as f:
        f.write(install_script)
    
    # Сделать скрипт исполняемым
    os.chmod(base_dir / "install" / "install.sh", 0o755)
    
    # Создание systemd службы
    service_content = '''[Unit]
Description=SIEM Security Agent
After=network.target

[Service]
Type=simple
User=siem-agent
Group=siem-agent
WorkingDirectory=/opt/siem-agent/agent
ExecStart=/usr/bin/python3 /opt/siem-agent/agent/windows_agent.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
'''
    
    with open(base_dir / "service" / "siem-agent.service", "w") as f:
        f.write(service_content)
    
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

logging:
  level: "INFO"
  file: "/var/log/siem-agent/agent.log"
  max_size_mb: 10
  backup_count: 5
'''
    
    with open(base_dir / "config" / "agent.example.yaml", "w") as f:
        f.write(config_example)
    
    # Создание README для Astra Linux 1.7
    readme = '''# SIEM Astra Linux Agent v2.0.0 - Офлайн Репозиторий для Astra Linux 1.7

## Описание
Офлайн репозиторий для развертывания SIEM агента на Astra Linux 1.7 системах без доступа к интернету.

## Совместимость
- ✅ Astra Linux 1.7 (Python 3.7.3)
- ✅ Python 3.7+
- ✅ systemd
- ✅ Полностью офлайн установка

## Содержимое
- `agent/` - Исходный код агента
- `packages/` - Python пакеты для Python 3.7
- `install/` - Скрипты установки
- `config/` - Конфигурационные файлы

## Требования
- Astra Linux 1.7
- Python 3.7+ (включен в Astra Linux 1.7)
- Root права для установки

## Установка

### Автоматическая установка
1. Распакуйте архив в любую папку
2. Запустите `sudo ./install/install.sh`
3. Настройте конфигурацию в `/opt/siem-agent/config/agent.yaml`
4. Служба запустится автоматически

### Ручная установка
1. Установите системные пакеты:
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pip python3-setuptools python3-wheel
   ```

2. Скопируйте папку agent в /opt/siem-agent/
3. Установите зависимости:
   ```bash
   cd /opt/siem-agent/agent
   pip3 install -r requirements_astra_1.7.txt
   ```
4. Настройте конфигурацию
5. Запустите агента: `python3 windows_agent.py`

## Конфигурация
Отредактируйте файл `/opt/siem-agent/config/agent.yaml`:
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
- Запуск: `sudo systemctl start siem-agent`
- Остановка: `sudo systemctl stop siem-agent`
- Статус: `sudo systemctl status siem-agent`
- Логи: `sudo journalctl -u siem-agent -f`

## Поддерживаемые функции
- Сбор системных метрик (CPU, память, диск, сеть)
- Мониторинг процессов
- Сбор сетевых подключений
- Системные логи

## Особенности для Astra Linux 1.7
- Использует Python 3.7 совместимые версии пакетов
- Проверяет версию Python перед установкой
- Оптимизирован для Astra Linux 1.7

## Лицензия
Proprietary - SIEM Security System
'''
    
    with open(base_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    
    # Создание манифеста
    manifest = {
        "name": "SIEM Astra Linux Agent",
        "version": "2.0.0",
        "platform": "astra-linux-1.7",
        "python_version": "3.7+",
        "dependencies": [
            "requests>=2.25.0,<3.0.0",
            "PyYAML>=5.4.0,<6.0.0",
            "psutil>=5.8.0,<6.0.0",
            "scapy>=2.4.0,<3.0.0"
        ],
        "install_script": "install/install.sh",
        "config_file": "config/agent.yaml",
        "service_name": "siem-agent"
    }
    
    with open(base_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

def create_zip_archive():
    """Создание ZIP архива"""
    print("Creating ZIP archive...")
    
    base_dir = Path("offline_repos/astra/siem-astra-agent-v2.0.0")
    archive_path = "offline_repos/astra/siem-astra-agent-v2.0.0.zip"
    
    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(base_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(base_dir.parent)
                zipf.write(file_path, arcname)
    
    print(f"Archive created: {archive_path}")

def main():
    """Основная функция"""
    print("Building Astra Linux 1.7 offline repository...")
    
    # Создание базовой структуры
    create_astra_agent_1_7()
    
    # Скачивание зависимостей
    download_python_packages_astra_1_7()
    
    # Создание архива
    create_zip_archive()
    
    print("Astra Linux 1.7 repository build completed!")

if __name__ == "__main__":
    main()
