#!/usr/bin/env python3
"""
Скрипт для проверки статуса агентов и сбора данных
"""

import requests
import json
import sys
from datetime import datetime

def check_server_status():
    """Проверяет статус сервера SIEM"""
    try:
        headers = {"X-API-Key": "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"}
        response = requests.get("http://localhost:8000/api/dashboard/stats", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_agents():
    """Проверяет статус агентов"""
    try:
        headers = {"X-API-Key": "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"}
        response = requests.get("http://localhost:8000/api/network/agents", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_events():
    """Проверяет последние события"""
    try:
        headers = {"X-API-Key": "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"}
        response = requests.get("http://localhost:8000/api/events/recent?limit=10", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def check_alerts():
    """Проверяет последние алерты"""
    try:
        headers = {"X-API-Key": "690023318602ee078fb6d5cbe2a17f8bd5d99a8e4899d8765c5ad23828938beb"}
        response = requests.get("http://localhost:8000/api/alerts/recent?limit=10", headers=headers, timeout=5)
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"HTTP {response.status_code}"
    except Exception as e:
        return False, str(e)

def main():
    """Основная функция"""
    print("🛡️ SIEM System - Проверка статуса агентов")
    print("=" * 50)
    
    # Проверяем сервер
    print("🔍 Проверяем сервер SIEM...")
    server_ok, server_data = check_server_status()
    if server_ok:
        print("✅ Сервер SIEM работает")
        print(f"   Активных событий: {server_data.get('activeEvents', 0)}")
        print(f"   Заблокированных угроз: {server_data.get('blockedThreats', 0)}")
        print(f"   Критических алертов: {server_data.get('criticalAlerts', 0)}")
    else:
        print(f"❌ Сервер SIEM недоступен: {server_data}")
        return
    
    print()
    
    # Проверяем агентов
    print("🔍 Проверяем агентов...")
    agents_ok, agents_data = check_agents()
    if agents_ok:
        agents = agents_data.get('data', [])
        if agents:
            print(f"✅ Найдено агентов: {len(agents)}")
            for agent in agents:
                status_icon = "🟢" if agent.get('status') == 'online' else "🔴"
                print(f"   {status_icon} {agent.get('name', 'Unknown')} ({agent.get('ip', 'Unknown')}) - {agent.get('status', 'Unknown')}")
        else:
            print("⚠️ Агенты не найдены")
    else:
        print(f"❌ Ошибка получения агентов: {agents_data}")
    
    print()
    
    # Проверяем события
    print("🔍 Проверяем события...")
    events_ok, events_data = check_events()
    if events_ok:
        events = events_data.get('items', [])
        if events:
            print(f"✅ Найдено событий: {len(events)}")
            for event in events[:5]:  # Показываем только последние 5
                timestamp = event.get('timestamp', 'Unknown')
                event_type = event.get('event_type', 'Unknown')
                severity = event.get('severity', 'info')
                print(f"   📅 {timestamp} | {event_type} | {severity}")
        else:
            print("⚠️ События не найдены")
    else:
        print(f"❌ Ошибка получения событий: {events_data}")
    
    print()
    
    # Проверяем алерты
    print("🔍 Проверяем алерты...")
    alerts_ok, alerts_data = check_alerts()
    if alerts_ok:
        alerts = alerts_data.get('items', [])
        if alerts:
            print(f"✅ Найдено алертов: {len(alerts)}")
            for alert in alerts[:5]:  # Показываем только последние 5
                timestamp = alert.get('timestamp', 'Unknown')
                alert_type = alert.get('alert_type', 'Unknown')
                severity = alert.get('severity', 'info')
                print(f"   🚨 {timestamp} | {alert_type} | {severity}")
        else:
            print("⚠️ Алерты не найдены")
    else:
        print(f"❌ Ошибка получения алертов: {alerts_data}")
    
    print()
    print("=" * 50)
    
    # Общий статус
    if server_ok and agents_ok and events_ok:
        print("✅ Система работает корректно")
        print("🌐 Откройте http://localhost:3000 для просмотра интерфейса")
    else:
        print("❌ Обнаружены проблемы в работе системы")
        print("💡 Запустите агентов: python scripts/start_real_agents.py")

if __name__ == "__main__":
    main()
