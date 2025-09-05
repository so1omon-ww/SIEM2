#!/usr/bin/env python3
"""
SIEM Agent - основной скрипт для сбора и отправки событий безопасности
"""

import os
import sys
import time
import signal
import logging
import subprocess
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from collector.net_sniffer import NetSnifferCollector, SnifferConfig, _make_emitter
import sender

def setup_detailed_logging():
    """Настройка детального логирования для агента"""
    # Создаем форматтер для логов
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Очищаем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Консольный обработчик для INFO и выше
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # В Docker контейнере используем только консольное логирование
    # Файловое логирование отключено из-за ограничений контейнера
    
    # Настраиваем логгеры для модулей
    logging.getLogger("sender").setLevel(logging.DEBUG)
    logging.getLogger("NetSnifferCollector").setLevel(logging.DEBUG)
    logging.getLogger("agent").setLevel(logging.DEBUG)

def open_powershell_script(script_path: str) -> None:
    """
    Показывает информацию о требованиях для запуска агента
    """
    print("SIEM Agent Requirements:")
    print("Administrator privileges: Required")
    print("Scapy: Must be installed")
    print("Network access: For packet capture")
    print()
    print("Agent cannot work without administrator privileges")
    print("Run PowerShell as administrator and execute:")
    print("   python backend\\agents\\python\\agent.py")

def main():
    """Основная функция агента"""
    # Настройка детального логирования
    setup_detailed_logging()
    log = logging.getLogger("agent")
    
    # Конфигурация агента
    # В Docker используем имя сервиса, локально - localhost
    server_url = os.environ.get("SERVER_URL", "http://localhost:8000")
    host_id = os.environ.get("HOST_ID") or os.environ.get("COMPUTERNAME") or os.environ.get("HOSTNAME") or "unknown-host"
    api_key = os.environ.get("API_KEY") or os.environ.get("SIEM_API_KEY")
    
    # Валидация конфигурации
    if not api_key:
        log.error("API_KEY not set! Please set API_KEY environment variable or use run_local_agent.ps1")
        log.error("You can get API key from web interface: http://localhost:3000/register")
        sys.exit(1)
    
    if not server_url.startswith(('http://', 'https://')):
        log.error("Invalid SERVER_URL format: %s. Must start with http:// or https://", server_url)
        sys.exit(1)
    
    log.info("Agent starting: server=%s host_id=%s api_key=%s", server_url, host_id, "***" if api_key else "None")
    
    # Создаем emitter для отправки событий с логированием
    def logging_emitter(event: dict):
        """Emitter с детальным логированием"""
        log.debug("Sending event: %s", event.get('event_type', 'unknown'))
        log.debug("Event details: %s", event)
        
        try:
            # Отправляем через стандартный emitter
            emitter = _make_emitter(sender, server_url, api_key, False)
            emitter(event)
            log.info("Event sent successfully: %s", event.get('event_type', 'unknown'))
        except Exception as e:
            log.error("Error sending event: %s", e)
            log.exception("Full error traceback:")
    
    # Создаем конфигурацию для сниффера
    config = SnifferConfig(
        server_url=server_url,
        token=api_key,
        host_id=host_id,
        interface=None,  # автоопределение
        verify_tls=False,
        portscan_threshold=10,
        portscan_window_sec=60,
        min_severity="info",
        block_on_portscan=False,
        log_level="DEBUG"  # Увеличиваем уровень логирования
    )
    
    # Настройка обработчика сигналов для graceful shutdown
    def signal_handler(signum, frame):
        log.info("Получен сигнал завершения, останавливаю агент...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Проверяем, запущены ли мы в Docker
        is_docker = os.path.exists('/.dockerenv')
        
        if is_docker:
            log.info("Docker environment detected")
            log.info("Pausing 20 seconds for manual agent startup with administrator privileges...")
            log.info("To run agent locally with administrator privileges:")
            log.info("   1. Open PowerShell as administrator")
            log.info("   2. Navigate to agents/python folder")
            log.info("   3. Run: python agent.py")
            log.info("   4. Or use: .\\run_local_agent.ps1")
            
            # Countdown timer
            for i in range(20, 0, -1):
                log.info(f"Starting in {i} seconds...")
                time.sleep(1)
        
        # Initialize collector
        log.info("Initializing NetSnifferCollector...")
        collector = NetSnifferCollector(config, logging_emitter)
        
        # Start collector
        log.info("Starting NetSnifferCollector...")
        collector.start()
        log.info("Net sniffer collector started")
        
        # Main agent loop
        log.info("Agent is running. Press Ctrl+C to stop.")
        
        # Log status every 30 seconds
        last_status_log = time.time()
        
        while True:
            current_time = time.time()
            
            # Log status every 30 seconds
            if current_time - last_status_log >= 30:
                log.info("Agent active, waiting for events...")
                last_status_log = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        log.info("Received interrupt signal, stopping agent...")
    except Exception as e:
        log.error("Critical error in agent: %s", e)
        log.exception("Full error traceback:")
        sys.exit(1)
    finally:
        try:
            if 'collector' in locals():
                collector.stop()
                log.info("Collector stopped")
        except Exception as e:
            log.error("Error stopping collector: %s", e)

if __name__ == "__main__":
    main()
