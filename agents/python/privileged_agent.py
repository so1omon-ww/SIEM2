#!/usr/bin/env python3
"""
Привилегированный SIEM агент для Windows
Запускается в Docker контейнере с доступом к хостовой системе
"""

import os
import sys
import time
import json
import psutil
import socket
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests

# Импортируем Windows-специфичный сборщик
try:
    from windows_privileged_collector import WindowsPrivilegedCollector
except ImportError:
    WindowsPrivilegedCollector = None

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger("privileged_agent")

class PrivilegedWindowsCollector:
    """Сборщик данных Windows с привилегированным доступом"""
    
    def __init__(self, server_url: str, api_key: str):
        self.server_url = server_url
        self.api_key = api_key
        self.host_id = socket.gethostname()
        
        # Инициализируем Windows-специфичный сборщик если доступен
        self.windows_collector = None
        if WindowsPrivilegedCollector:
            try:
                self.windows_collector = WindowsPrivilegedCollector(self.host_id)
                log.info("Windows collector initialized")
            except Exception as e:
                log.warning(f"Не удалось инициализировать Windows сборщик: {e}")
        
    def collect_system_events(self) -> List[Dict[str, Any]]:
        """Сбор системных событий Windows"""
        events = []
        
        try:
            # Мониторинг процессов
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 'create_time']):
                try:
                    proc_info = proc.info
                    if proc_info['create_time'] and (time.time() - proc_info['create_time'] < 60):  # Новые процессы за последнюю минуту
                        event = {
                            "timestamp": datetime.utcnow().isoformat() + "Z",
                            "event_type": "process.created",
                            "source": "privileged_agent",
                            "host_id": self.host_id,
                            "severity": "info",
                            "details": {
                                "process": {
                                    "pid": proc_info['pid'],
                                    "name": proc_info['name'],
                                    "username": proc_info.get('username', 'unknown'),
                                    "command_line": ' '.join(proc_info.get('cmdline', [])) if proc_info.get('cmdline') else '',
                                    "created_at": datetime.fromtimestamp(proc_info['create_time']).isoformat()
                                }
                            }
                        }
                        events.append(event)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
                    
        except Exception as e:
            log.error(f"Ошибка сбора процессов: {e}")
            
        return events
    
    def collect_network_connections(self) -> List[Dict[str, Any]]:
        """Сбор сетевых соединений"""
        events = []
        
        try:
            connections = psutil.net_connections(kind='inet')
            for conn in connections:
                if conn.status == psutil.CONN_ESTABLISHED:
                    event = {
                        "timestamp": datetime.utcnow().isoformat() + "Z",
                        "event_type": "network.connection",
                        "source": "privileged_agent", 
                        "host_id": self.host_id,
                        "severity": "info",
                        "details": {
                            "connection": {
                                "local_addr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "unknown",
                                "remote_addr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "unknown",
                                "status": conn.status,
                                "pid": conn.pid,
                                "family": "IPv4" if conn.family == socket.AF_INET else "IPv6"
                            }
                        }
                    }
                    events.append(event)
                    
        except Exception as e:
            log.error(f"Ошибка сбора сетевых соединений: {e}")
            
        return events
    
    def collect_system_performance(self) -> List[Dict[str, Any]]:
        """Сбор данных производительности системы"""
        events = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            net_io = psutil.net_io_counters()
            
            event = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "event_type": "system.performance",
                "source": "privileged_agent",
                "host_id": self.host_id,
                "severity": "info",
                "details": {
                    "performance": {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available_gb": round(memory.available / (1024**3), 2),
                        "disk_read_mb": round(disk_io.read_bytes / (1024**2), 2) if disk_io else 0,
                        "disk_write_mb": round(disk_io.write_bytes / (1024**2), 2) if disk_io else 0,
                        "network_sent_mb": round(net_io.bytes_sent / (1024**2), 2) if net_io else 0,
                        "network_recv_mb": round(net_io.bytes_recv / (1024**2), 2) if net_io else 0
                    }
                }
            }
            events.append(event)
            
        except Exception as e:
            log.error(f"Ошибка сбора данных производительности: {e}")
            
        return events

    def collect_windows_events(self) -> List[Dict[str, Any]]:
        """Сбор Windows Event Log через PowerShell (если доступен)"""
        events = []
        
        try:
            # Проверяем, доступен ли PowerShell в контейнере
            if os.name == 'nt' or os.path.exists('/usr/bin/pwsh'):
                powershell_cmd = 'powershell' if os.name == 'nt' else 'pwsh'
                
                # Команда для получения последних событий безопасности
                ps_command = [
                    powershell_cmd, '-Command',
                    "Get-WinEvent -FilterHashtable @{LogName='Security'; StartTime=(Get-Date).AddMinutes(-5)} -MaxEvents 10 -ErrorAction SilentlyContinue | ConvertTo-Json"
                ]
                
                result = subprocess.run(ps_command, capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and result.stdout.strip():
                    try:
                        win_events = json.loads(result.stdout)
                        if not isinstance(win_events, list):
                            win_events = [win_events]
                            
                        for win_event in win_events:
                            event = {
                                "timestamp": datetime.utcnow().isoformat() + "Z",
                                "event_type": "windows.security_event",
                                "source": "privileged_agent",
                                "host_id": self.host_id,
                                "severity": "warning" if win_event.get('LevelDisplayName') == 'Warning' else "info",
                                "details": {
                                    "windows_event": {
                                        "event_id": win_event.get('Id'),
                                        "level": win_event.get('LevelDisplayName'),
                                        "log_name": win_event.get('LogName'),
                                        "provider_name": win_event.get('ProviderName'),
                                        "message": win_event.get('Message', '')[:500]  # Ограничиваем длину
                                    }
                                }
                            }
                            events.append(event)
                    except json.JSONDecodeError:
                        log.warning("Не удалось распарсить JSON от PowerShell")
                        
        except Exception as e:
            log.debug(f"PowerShell недоступен или ошибка: {e}")
            
        return events

    def send_events(self, events: List[Dict[str, Any]]) -> bool:
        """Отправка событий на сервер"""
        if not events:
            return True
            
        try:
            url = f"{self.server_url}/api/events/ingest/batch"
            headers = {
                "Content-Type": "application/json",
                "X-API-Key": self.api_key
            }
            
            response = requests.post(
                url, 
                json={"items": events}, 
                headers=headers,
                timeout=10,
                verify=False
            )
            
            if response.status_code == 200:
                log.info(f"Sent {len(events)} events successfully")
                return True
            else:
                log.error(f"Failed to send events: {response.status_code} {response.text}")
                return False
                
        except Exception as e:
            log.error(f"Error sending events: {e}")
            return False

def main():
    """Основная функция привилегированного агента"""
    
    # Получаем конфигурацию из переменных окружения
    server_url = os.environ.get("SERVER_URL", "http://backend:8000")
    api_key = os.environ.get("API_KEY") or os.environ.get("SIEM_API_KEY") or "3ac0f6cfbe0d9c663fc86a922aacb018543cb3f5fdd882bd680821bb60bbc7da"
    
    if not api_key:
        log.error("API_KEY not set!")
        sys.exit(1)
    
    log.info("Privileged agent started")
    log.info(f"Server: {server_url}")
    log.info(f"API key: {'***' if api_key else 'NOT SET'}")
    log.info(f"Host: {socket.gethostname()}")
    log.info(f"Python: {sys.version}")
    log.info(f"Privileges: {'ROOT' if os.geteuid() == 0 else 'USER'}" if hasattr(os, 'geteuid') else "WINDOWS")
    
    collector = PrivilegedWindowsCollector(server_url, api_key)
    
    log.info("Starting data collection...")
    
    while True:
        try:
            all_events = []
            
            # Collect different types of events
            log.debug("Collecting system events...")
            all_events.extend(collector.collect_system_events())
            
            log.debug("Collecting network connections...")
            all_events.extend(collector.collect_network_connections())
            
            log.debug("Collecting performance data...")
            all_events.extend(collector.collect_system_performance())
            
            log.debug("Collecting Windows events...")
            all_events.extend(collector.collect_windows_events())
            
            # Use Windows-specific collector if available
            if collector.windows_collector:
                log.debug("Collecting Windows Security Events...")
                all_events.extend(collector.windows_collector.collect_security_events())
                
                log.debug("Collecting Windows System Events...")
                all_events.extend(collector.windows_collector.collect_system_events())
                
                log.debug("Collecting Windows Process Creation Events...")
                all_events.extend(collector.windows_collector.collect_process_creation_events())
                
                log.debug("Collecting Windows Network Activity...")
                all_events.extend(collector.windows_collector.collect_network_activity())
            
            # Send events
            if all_events:
                success = collector.send_events(all_events)
                if success:
                    log.info(f"Collected and sent {len(all_events)} events")
                else:
                    log.warning(f"Failed to send {len(all_events)} events")
            else:
                log.info("No new events to send")
            
            # Wait between collection cycles
            time.sleep(30)
            
        except KeyboardInterrupt:
            log.info("Received shutdown signal")
            break
        except Exception as e:
            log.error(f"Error in main loop: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
