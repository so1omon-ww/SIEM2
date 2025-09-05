#!/usr/bin/env python3
"""
Скрипт для запуска реальных агентов сбора данных
"""

import subprocess
import sys
import os
import time
import signal
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

def start_agent(agent_type: str, config_file: str = None):
    """Запускает агент указанного типа"""
    agents_dir = Path(__file__).parent.parent / "agents" / "python"
    
    if agent_type == "windows":
        script_path = agents_dir / "windows_agent.py"
        config_file = config_file or agents_dir / "secagent.example.yaml"
    elif agent_type == "privileged":
        script_path = agents_dir / "privileged_agent.py"
        config_file = config_file or agents_dir / "config.yaml"
    else:
        script_path = agents_dir / "agent.py"
        config_file = config_file or agents_dir / "config.yaml"
    
    if not script_path.exists():
        print(f"❌ Агент {agent_type} не найден: {script_path}")
        return None
    
    if not config_file or not Path(config_file).exists():
        print(f"❌ Конфигурационный файл не найден: {config_file}")
        return None
    
    # Устанавливаем переменные окружения
    env = os.environ.copy()
    env["SERVER_URL"] = "http://localhost:8000"
    env["API_KEY"] = "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"
    
    try:
        print(f"🚀 Запускаем агент {agent_type}...")
        print(f"   Скрипт: {script_path}")
        print(f"   Конфиг: {config_file}")
        
        # Запускаем агент
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            cwd=str(agents_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        print(f"✅ Агент {agent_type} запущен (PID: {process.pid})")
        return process
        
    except Exception as e:
        print(f"❌ Ошибка запуска агента {agent_type}: {e}")
        return None

def stop_agent(process):
    """Останавливает агент"""
    if process and process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=5)
            print(f"✅ Агент остановлен")
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"⚠️ Агент принудительно остановлен")
        except Exception as e:
            print(f"❌ Ошибка остановки агента: {e}")

def main():
    """Основная функция"""
    print("🛡️ SIEM System - Запуск реальных агентов")
    print("=" * 50)
    
    # Проверяем, что сервер запущен
    try:
        import requests
        headers = {"X-API-Key": "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"}
        response = requests.get("http://localhost:8000/api/dashboard/stats", headers=headers, timeout=5)
        if response.status_code != 200:
            print("❌ Сервер SIEM не запущен или недоступен")
            print("   Запустите: docker-compose -f infra/docker/docker-compose.yml up -d")
            return
    except Exception as e:
        print("❌ Не удается подключиться к серверу SIEM")
        print(f"   Ошибка: {e}")
        print("   Запустите: docker-compose -f infra/docker/docker-compose.yml up -d")
        return
    
    print("✅ Сервер SIEM доступен")
    
    # Список агентов для запуска
    agents_to_start = [
        ("windows", "Windows Agent"),
        ("privileged", "Privileged Agent")
    ]
    
    processes = []
    
    try:
        # Запускаем агентов
        for agent_type, agent_name in agents_to_start:
            process = start_agent(agent_type)
            if process:
                processes.append((agent_type, process))
                time.sleep(2)  # Небольшая задержка между запусками
        
        if not processes:
            print("❌ Не удалось запустить ни одного агента")
            return
        
        print(f"\n✅ Запущено агентов: {len(processes)}")
        print("📊 Агенты начали сбор данных...")
        print("\nДля остановки нажмите Ctrl+C")
        
        # Мониторим процессы
        while True:
            time.sleep(5)
            
            # Проверяем, что все процессы еще работают
            active_processes = []
            for agent_type, process in processes:
                if process.poll() is None:
                    active_processes.append((agent_type, process))
                else:
                    print(f"⚠️ Агент {agent_type} завершился (код: {process.returncode})")
            
            processes = active_processes
            
            if not processes:
                print("❌ Все агенты завершились")
                break
            
            # Показываем статистику
            try:
                headers = {"X-API-Key": "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"}
                response = requests.get("http://localhost:8000/api/dashboard/stats", headers=headers, timeout=5)
                if response.status_code == 200:
                    stats = response.json()
                    print(f"📈 Активных событий: {stats.get('activeEvents', 0)}")
            except:
                pass
    
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал остановки...")
    
    finally:
        # Останавливаем всех агентов
        print("\n🛑 Останавливаем агентов...")
        for agent_type, process in processes:
            print(f"   Останавливаем {agent_type}...")
            stop_agent(process)
        
        print("✅ Все агенты остановлены")

if __name__ == "__main__":
    main()
