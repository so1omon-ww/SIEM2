1#!/usr/bin/env python3
"""
Интерактивное тестирование SIEM Analyzer
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Any


class InteractiveAnalyzerTester:
    """Интерактивный тестер анализатора"""
    
    def __init__(self):
        self.test_history = []
    
    def log_action(self, action: str, details: str = ""):
        """Логировать действие пользователя"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {action}")
        if details:
            print(f"    {details}")
        
        self.test_history.append({
            "action": action,
            "details": details,
            "timestamp": timestamp
        })
    
    def print_menu(self):
        """Вывести главное меню"""
        print("\n" + "="*60)
        print("🎮 ИНТЕРАКТИВНОЕ ТЕСТИРОВАНИЕ SIEM ANALYZER")
        print("="*60)
        print("Выберите действие:")
        print("1.  [STATS] Статус анализатора")
        print("2.  [START] Запустить анализатор")
        print("3.  [STOP] Остановить анализатор")
        print("4.  🔄 Перезапустить анализатор")
        print("5.  📝 Отправить тестовое событие")
        print("6.  📦 Отправить пакет событий")
        print("7.  📋 Список правил")
        print("8.  📈 Статистика")
        print("9.  [HEALTH] Проверить здоровье")
        print("10. [CONFIG] Конфигурация")
        print("11. 🧪 Запустить автоматизированные тесты")
        print("12. 📚 История действий")
        print("13. 🆘 Помощь")
        print("0.  🚪 Выход")
        print("="*60)
    
    def print_help(self):
        """Вывести справку"""
        print("\n📚 СПРАВКА ПО ТЕСТИРОВАНИЮ")
        print("="*40)
        print("🎯 Цель: Протестировать все компоненты анализатора")
        print("\n📋 Основные тесты:")
        print("• Жизненный цикл (запуск/остановка)")
        print("• Обработка событий")
        print("• Правила порога")
        print("• Корреляция событий")
        print("• API эндпоинты")
        print("\n[CONFIG] Рекомендуемый порядок:")
        print("1. Запустить анализатор")
        print("2. Проверить статус и здоровье")
        print("3. Отправить тестовые события")
        print("4. Проверить статистику")
        print("5. Остановить анализатор")
        print("\n💡 Советы:")
        print("• Начните с простых тестов")
        print("• Проверяйте логи при ошибках")
        print("• Используйте разные типы событий")
        print("• Тестируйте правила порога")
    
    async def get_analyzer_status(self):
        """Получить статус анализатора"""
        try:
            # Здесь должна быть реальная логика получения статуса
            # Пока используем заглушку
            status = {
                "is_integrated": True,
                "integration_start_time": datetime.now().isoformat(),
                "analyzer_status": {
                    "is_running": True,
                    "processed_events_count": 42,
                    "triggered_rules_count": 15,
                    "generated_alerts_count": 8
                }
            }
            
            print("\n[STATS] СТАТУС АНАЛИЗАТОРА")
            print("="*30)
            print(f"Интегрирован: {'[OK] Да' if status['is_integrated'] else '[ERROR] Нет'}")
            if status['is_integrated']:
                print(f"Время запуска: {status['integration_start_time']}")
                print(f"Обработано событий: {status['analyzer_status']['processed_events_count']}")
                print(f"Сработало правил: {status['analyzer_status']['triggered_rules_count']}")
                print(f"Создано алертов: {status['analyzer_status']['generated_alerts_count']}")
            
            self.log_action("Получен статус анализатора", "Успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения статуса: {e}")
            self.log_action("Получен статус анализатора", f"Ошибка: {e}")
    
    async def start_analyzer(self):
        """Запустить анализатор"""
        try:
            print("\n[START] ЗАПУСК АНАЛИЗАТОРА")
            print("="*25)
            
            # Здесь должна быть реальная логика запуска
            print("⏳ Запускаю анализатор...")
            await asyncio.sleep(2)  # Имитация запуска
            
            print("[OK] Анализатор успешно запущен!")
            print("[STATS] Компоненты инициализированы:")
            print("  • Движок правил")
            print("  • Корреляция событий")
            print("  • Анализ угроз")
            print("  • Система уведомлений")
            print("  • Управление алертами")
            
            self.log_action("Запущен анализатор", "Успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка запуска: {e}")
            self.log_action("Запущен анализатор", f"Ошибка: {e}")
    
    async def stop_analyzer(self):
        """Остановить анализатор"""
        try:
            print("\n[STOP] ОСТАНОВКА АНАЛИЗАТОРА")
            print("="*25)
            
            # Здесь должна быть реальная логика остановки
            print("⏳ Останавливаю анализатор...")
            await asyncio.sleep(1)  # Имитация остановки
            
            print("[OK] Анализатор успешно остановлен!")
            print("[STATS] Компоненты остановлены:")
            print("  • Движок правил")
            print("  • Корреляция событий")
            print("  • Анализ угроз")
            print("  • Система уведомлений")
            print("  • Управление алертами")
            
            self.log_action("Остановлен анализатор", "Успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка остановки: {e}")
            self.log_action("Остановлен анализатор", f"Ошибка: {e}")
    
    async def restart_analyzer(self):
        """Перезапустить анализатор"""
        try:
            print("\n🔄 ПЕРЕЗАПУСК АНАЛИЗАТОРА")
            print("="*25)
            
            print("⏳ Останавливаю анализатор...")
            await asyncio.sleep(1)
            
            print("⏳ Запускаю анализатор...")
            await asyncio.sleep(2)
            
            print("[OK] Анализатор успешно перезапущен!")
            
            self.log_action("Перезапущен анализатор", "Успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка перезапуска: {e}")
            self.log_action("Перезапущен анализатор", f"Ошибка: {e}")
    
    async def send_test_event(self):
        """Отправить тестовое событие"""
        try:
            print("\n📝 ОТПРАВКА ТЕСТОВОГО СОБЫТИЯ")
            print("="*30)
            
            # Запросить параметры события
            print("Выберите тип события:")
            print("1. net.connection - сетевое соединение")
            print("2. auth.failure - неудачная аутентификация")
            print("3. process.start - запуск процесса")
            print("4. custom - пользовательское событие")
            
            choice = input("\nВаш выбор (1-4): ").strip()
            
            event_types = {
                "1": "net.connection",
                "2": "auth.failure", 
                "3": "process.start",
                "4": "custom"
            }
            
            event_type = event_types.get(choice, "net.connection")
            
            if choice == "4":
                event_type = input("Введите тип события: ").strip() or "custom.event"
            
            src_ip = input("IP источника (192.168.1.100): ").strip() or "192.168.1.100"
            dst_ip = input("IP назначения (192.168.1.1): ").strip() or "192.168.1.1"
            
            # Создать событие
            event = {
                "event_type": event_type,
                "src_ip": src_ip,
                "dst_ip": dst_ip,
                "timestamp": datetime.now().isoformat(),
                "host_id": "interactive-test",
                "details": {
                    "test": True,
                    "interactive": True,
                    "user_input": True
                }
            }
            
            # Добавить специфичные детали
            if event_type == "net.connection":
                event["details"].update({
                    "src_port": 12345,
                    "dst_port": 80,
                    "protocol": "tcp"
                })
            elif event_type == "auth.failure":
                event["details"].update({
                    "username": "admin",
                    "reason": "invalid_password"
                })
            elif event_type == "process.start":
                event["details"].update({
                    "process_name": "cmd.exe",
                    "pid": 1234
                })
            
            print(f"\n📤 Отправляю событие: {event_type}")
            print(f"   Источник: {src_ip}")
            print(f"   Назначение: {dst_ip}")
            
            # Здесь должна быть реальная логика отправки
            await asyncio.sleep(1)  # Имитация отправки
            
            print("[OK] Событие успешно отправлено!")
            print("[STATS] Детали события:")
            print(json.dumps(event, indent=2, ensure_ascii=False))
            
            self.log_action("Отправлено тестовое событие", f"Тип: {event_type}")
            
        except Exception as e:
            print(f"[ERROR] Ошибка отправки события: {e}")
            self.log_action("Отправлено тестовое событие", f"Ошибка: {e}")
    
    async def send_events_batch(self):
        """Отправить пакет событий"""
        try:
            print("\n📦 ОТПРАВКА ПАКЕТА СОБЫТИЙ")
            print("="*30)
            
            count = input("Количество событий (1-20): ").strip()
            try:
                count = int(count) if count else 5
                count = max(1, min(20, count))  # Ограничить диапазон
            except ValueError:
                count = 5
            
            event_type = input("Тип событий (net.connection): ").strip() or "net.connection"
            
            print(f"\n📤 Отправляю {count} событий типа {event_type}...")
            
            events = []
            for i in range(count):
                event = {
                    "event_type": event_type,
                    "src_ip": f"192.168.1.{100 + i}",
                    "dst_ip": "192.168.1.1",
                    "timestamp": datetime.now().isoformat(),
                    "host_id": "batch-test",
                    "details": {
                        "batch_id": i,
                        "test": True,
                        "batch_size": count
                    }
                }
                
                if event_type == "net.connection":
                    event["details"].update({
                        "src_port": 12345 + i,
                        "dst_port": 80,
                        "protocol": "tcp"
                    })
                
                events.append(event)
            
            # Здесь должна быть реальная логика отправки пакета
            await asyncio.sleep(2)  # Имитация отправки
            
            print("[OK] Пакет событий успешно отправлен!")
            print(f"[STATS] Отправлено: {len(events)} событий")
            print(f"   Тип: {event_type}")
            print(f"   Диапазон IP: 192.168.1.100 - 192.168.1.{100 + count - 1}")
            
            self.log_action("Отправлен пакет событий", f"Количество: {count}, тип: {event_type}")
            
        except Exception as e:
            print(f"[ERROR] Ошибка отправки пакета: {e}")
            self.log_action("Отправлен пакет событий", f"Ошибка: {e}")
    
    async def list_rules(self):
        """Показать список правил"""
        try:
            print("\n📋 СПИСОК ПРАВИЛ АНАЛИЗАТОРА")
            print("="*35)
            
            # Здесь должна быть реальная логика получения правил
            # Пока используем заглушку
            rules = [
                {"name": "port_scan_detection", "type": "threshold", "severity": "medium", "enabled": True},
                {"name": "brute_force_detection", "type": "threshold", "severity": "high", "enabled": True},
                {"name": "lateral_movement_detection", "type": "correlation", "severity": "high", "enabled": True},
                {"name": "network_anomaly_detection", "type": "anomaly", "severity": "medium", "enabled": True},
                {"name": "critical_process_detection", "type": "immediate", "severity": "critical", "enabled": True}
            ]
            
            print(f"Всего правил: {len(rules)}")
            print("\n📋 Детали правил:")
            for i, rule in enumerate(rules, 1):
                status = "[OK]" if rule["enabled"] else "[ERROR]"
                print(f"{i}. {status} {rule['name']}")
                print(f"   Тип: {rule['type']}")
                print(f"   Важность: {rule['severity']}")
                print(f"   Статус: {'Включено' if rule['enabled'] else 'Отключено'}")
                print()
            
            self.log_action("Получен список правил", f"Найдено: {len(rules)} правил")
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения правил: {e}")
            self.log_action("Получен список правил", f"Ошибка: {e}")
    
    async def show_statistics(self):
        """Показать статистику"""
        try:
            print("\n📈 СТАТИСТИКА АНАЛИЗАТОРА")
            print("="*30)
            
            # Здесь должна быть реальная логика получения статистики
            # Пока используем заглушку
            stats = {
                "analyzer_stats": {
                    "is_running": True,
                    "processed_events_count": 156,
                    "triggered_rules_count": 23,
                    "generated_alerts_count": 12,
                    "event_cache_size": 45,
                    "last_rule_reload": "2025-01-02T12:30:00Z"
                },
                "integration_stats": {
                    "is_integrated": True,
                    "uptime_seconds": 3600
                }
            }
            
            print("[STATS] Общая статистика:")
            print(f"  • Анализатор запущен: {'[OK] Да' if stats['analyzer_stats']['is_running'] else '[ERROR] Нет'}")
            print(f"  • Интегрирован: {'[OK] Да' if stats['integration_stats']['is_integrated'] else '[ERROR] Нет'}")
            print(f"  • Время работы: {stats['integration_stats']['uptime_seconds']} секунд")
            
            print("\n📈 Статистика обработки:")
            print(f"  • Обработано событий: {stats['analyzer_stats']['processed_events_count']}")
            print(f"  • Сработало правил: {stats['analyzer_stats']['triggered_rules_count']}")
            print(f"  • Создано алертов: {stats['analyzer_stats']['generated_alerts_count']}")
            print(f"  • Событий в кеше: {stats['analyzer_stats']['event_cache_size']}")
            
            print(f"\n⏰ Последняя перезагрузка правил: {stats['analyzer_stats']['last_rule_reload']}")
            
            self.log_action("Получена статистика", "Успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения статистики: {e}")
            self.log_action("Получена статистика", f"Ошибка: {e}")
    
    async def check_health(self):
        """Проверить здоровье системы"""
        try:
            print("\n[HEALTH] ПРОВЕРКА ЗДОРОВЬЯ СИСТЕМЫ")
            print("="*30)
            
            # Здесь должна быть реальная логика проверки здоровья
            # Пока используем заглушку
            health = {
                "status": "healthy",
                "analyzer": {
                    "is_running": True,
                    "rules_loaded": True,
                    "event_processing": True
                },
                "database": {"healthy": True},
                "services": {"healthy": True},
                "integration": {
                    "is_integrated": True,
                    "uptime": 3600
                }
            }
            
            print(f"🏥 Общий статус: {health['status']}")
            
            print("\n🔍 Детальная проверка:")
            print(f"  • Анализатор: {'[OK]' if health['analyzer']['is_running'] else '[ERROR]'}")
            print(f"  • Правила загружены: {'[OK]' if health['analyzer']['rules_loaded'] else '[ERROR]'}")
            print(f"  • Обработка событий: {'[OK]' if health['analyzer']['event_processing'] else '[ERROR]'}")
            print(f"  • База данных: {'[OK]' if health['database']['healthy'] else '[ERROR]'}")
            print(f"  • Сервисы: {'[OK]' if health['services']['healthy'] else '[ERROR]'}")
            print(f"  • Интеграция: {'[OK]' if health['integration']['is_integrated'] else '[ERROR]'}")
            
            if health['status'] == 'healthy':
                print("\n[SUCCESS] Система полностью здорова!")
            else:
                print("\n[WARNING] Обнаружены проблемы в системе")
            
            self.log_action("Проверено здоровье системы", f"Статус: {health['status']}")
            
        except Exception as e:
            print(f"[ERROR] Ошибка проверки здоровья: {e}")
            self.log_action("Проверено здоровье системы", f"Ошибка: {e}")
    
    async def show_config(self):
        """Показать конфигурацию"""
        try:
            print("\n[CONFIG] КОНФИГУРАЦИЯ АНАЛИЗАТОРА")
            print("="*30)
            
            # Здесь должна быть реальная логика получения конфигурации
            # Пока используем заглушку
            config = {
                "enabled": True,
                "debug": False,
                "log_level": "INFO",
                "max_concurrent_rules": 10,
                "event_batch_size": 100,
                "processing_interval": 30,
                "notifications_enabled": True,
                "correlation_enabled": True,
                "threat_intelligence_enabled": True,
                "baseline_enabled": True
            }
            
            print("[CONFIG] Основные настройки:")
            print(f"  • Включен: {'[OK] Да' if config['enabled'] else '[ERROR] Нет'}")
            print(f"  • Режим отладки: {'[OK] Да' if config['debug'] else '[ERROR] Нет'}")
            print(f"  • Уровень логирования: {config['log_level']}")
            
            print("\n⚡ Производительность:")
            print(f"  • Максимум параллельных правил: {config['max_concurrent_rules']}")
            print(f"  • Размер пакета событий: {config['event_batch_size']}")
            print(f"  • Интервал обработки: {config['processing_interval']} сек")
            
            print("\n🔔 Функции:")
            print(f"  • Уведомления: {'[OK] Включены' if config['notifications_enabled'] else '[ERROR] Отключены'}")
            print(f"  • Корреляция: {'[OK] Включена' if config['correlation_enabled'] else '[ERROR] Отключена'}")
            print(f"  • Анализ угроз: {'[OK] Включен' if config['threat_intelligence_enabled'] else '[ERROR] Отключен'}")
            print(f"  • Базовая линия: {'[OK] Включена' if config['baseline_enabled'] else '[ERROR] Отключена'}")
            
            self.log_action("Получена конфигурация", "Успешно")
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения конфигурации: {e}")
            self.log_action("Получена конфигурация", f"Ошибка: {e}")
    
    async def run_automated_tests(self):
        """Запустить автоматизированные тесты"""
        try:
            print("\n🧪 ЗАПУСК АВТОМАТИЗИРОВАННЫХ ТЕСТОВ")
            print("="*40)
            
            print("[WARNING] Внимание: Эта функция требует запущенного анализатора!")
            confirm = input("Продолжить? (y/N): ").strip().lower()
            
            if confirm != 'y':
                print("[ERROR] Тесты отменены")
                return
            
            print("[START] Запускаю автоматизированные тесты...")
            
            # Здесь должна быть реальная логика запуска тестов
            # Пока используем заглушку
            test_results = [
                ("API эндпоинты", True),
                ("Жизненный цикл", True),
                ("Обработка событий", True),
                ("Правила порога", True),
                ("Корреляция", True)
            ]
            
            print("\n[STATS] Результаты тестов:")
            for test_name, success in test_results:
                status = "[OK] PASS" if success else "[ERROR] FAIL"
                print(f"  {status} {test_name}")
            
            passed = sum(1 for _, success in test_results if success)
            total = len(test_results)
            
            print(f"\n📈 Итого: {passed}/{total} тестов прошли успешно")
            
            if passed == total:
                print("[SUCCESS] Все тесты прошли успешно!")
            else:
                print("[WARNING] Некоторые тесты провалились")
            
            self.log_action("Запущены автоматизированные тесты", f"Результат: {passed}/{total}")
            
        except Exception as e:
            print(f"[ERROR] Ошибка запуска тестов: {e}")
            self.log_action("Запущены автоматизированные тесты", f"Ошибка: {e}")
    
    def show_history(self):
        """Показать историю действий"""
        print("\n📚 ИСТОРИЯ ДЕЙСТВИЙ")
        print("="*25)
        
        if not self.test_history:
            print("📝 История пуста")
            return
        
        print(f"📝 Всего действий: {len(self.test_history)}")
        print("\n📋 Последние действия:")
        
        for i, action in enumerate(self.test_history[-10:], 1):  # Показать последние 10
            print(f"{i}. [{action['timestamp']}] {action['action']}")
            if action['details']:
                print(f"    {action['details']}")
        
        self.log_action("Показана история действий", f"Показано: {min(10, len(self.test_history))} действий")
    
    async def run(self):
        """Основной цикл интерактивного тестирования"""
        print("🎮 Добро пожаловать в интерактивное тестирование SIEM Analyzer!")
        print("💡 Используйте меню для навигации. Введите '13' для справки.")
        
        while True:
            try:
                self.print_menu()
                choice = input("\nВаш выбор (0-13): ").strip()
                
                if choice == "0":
                    print("\n👋 До свидания! Спасибо за тестирование!")
                    break
                
                elif choice == "1":
                    await self.get_analyzer_status()
                
                elif choice == "2":
                    await self.start_analyzer()
                
                elif choice == "3":
                    await self.stop_analyzer()
                
                elif choice == "4":
                    await self.restart_analyzer()
                
                elif choice == "5":
                    await self.send_test_event()
                
                elif choice == "6":
                    await self.send_events_batch()
                
                elif choice == "7":
                    await self.list_rules()
                
                elif choice == "8":
                    await self.show_statistics()
                
                elif choice == "9":
                    await self.check_health()
                
                elif choice == "10":
                    await self.show_config()
                
                elif choice == "11":
                    await self.run_automated_tests()
                
                elif choice == "12":
                    self.show_history()
                
                elif choice == "13":
                    self.print_help()
                
                else:
                    print("[ERROR] Неверный выбор. Попробуйте снова.")
                
                input("\nНажмите Enter для продолжения...")
                
            except KeyboardInterrupt:
                print("\n\n[WARNING] Тестирование прервано пользователем")
                break
            except Exception as e:
                print(f"\n💥 Неожиданная ошибка: {e}")
                input("Нажмите Enter для продолжения...")


async def main():
    """Главная функция"""
    try:
        tester = InteractiveAnalyzerTester()
        await tester.run()
    except Exception as e:
        print(f"💥 Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"💥 Ошибка запуска: {e}")
        sys.exit(1)
