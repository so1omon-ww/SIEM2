#!/usr/bin/env python3
"""
Автоматизированное тестирование SIEM Analyzer
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Any


class AnalyzerTester:
    """Класс для автоматизированного тестирования анализатора"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Логировать результат теста"""
        status = "[OK] PASS" if success else "[ERROR] FAIL"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {status} {test_name}")
        if details:
            print(f"    {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": timestamp
        })
    
    async def test_analyzer_lifecycle(self) -> bool:
        """Тест полного жизненного цикла анализатора"""
        print("\n🧪 Тестирование жизненного цикла анализатора...")
        
        try:
            # 1. Проверить начальный статус
            status = await self.get_status()
            initial_status = status.get('is_integrated', False)
            self.log_test("Начальный статус", True, f"Анализатор {'запущен' if initial_status else 'остановлен'}")
            
            # 2. Запустить анализатор
            start_result = await self.start_analyzer()
            if start_result.get('status') in ['starting', 'running']:
                self.log_test("Запуск анализатора", True, start_result.get('message', ''))
            else:
                self.log_test("Запуск анализатора", False, f"Неожиданный статус: {start_result}")
                return False
            
            # 3. Подождать запуска
            print("    ⏳ Ожидание запуска анализатора...")
            await asyncio.sleep(5)
            
            # 4. Проверить статус после запуска
            status = await self.get_status()
            if status.get('is_integrated', False):
                self.log_test("Статус после запуска", True, "Анализатор успешно запущен")
            else:
                self.log_test("Статус после запуска", False, "Анализатор не запустился")
                return False
            
            # 5. Проверить здоровье
            health = await self.health_check()
            if health.get('status') == 'healthy':
                self.log_test("Проверка здоровья", True, "Система здорова")
            else:
                self.log_test("Проверка здоровья", False, f"Статус здоровья: {health.get('status')}")
            
            # 6. Получить правила
            rules = await self.get_rules()
            total_rules = rules.get('total_rules', 0)
            if total_rules > 0:
                self.log_test("Загрузка правил", True, f"Загружено {total_rules} правил")
            else:
                self.log_test("Загрузка правил", False, "Правила не загружены")
            
            # 7. Протестировать обработку событий
            event_test_success = await self.test_event_processing()
            
            # 8. Получить статистику
            stats = await self.get_stats()
            processed_count = stats.get('analyzer_stats', {}).get('processed_events_count', 0)
            self.log_test("Получение статистики", True, f"Обработано {processed_count} событий")
            
            # 9. Остановить анализатор
            stop_result = await self.stop_analyzer()
            if stop_result.get('status') == 'stopped':
                self.log_test("Остановка анализатора", True, stop_result.get('message', ''))
            else:
                self.log_test("Остановка анализатора", False, f"Неожиданный статус: {stop_result}")
            
            print("[OK] Тест жизненного цикла завершен!")
            return True
            
        except Exception as e:
            self.log_test("Жизненный цикл", False, f"Ошибка: {str(e)}")
            return False
    
    async def test_event_processing(self) -> bool:
        """Тест обработки различных типов событий"""
        print("\n🔍 Тестирование обработки событий...")
        
        try:
            test_events = [
                # Сетевое соединение
                {
                    "event_type": "net.connection",
                    "src_ip": "192.168.1.100",
                    "dst_ip": "192.168.1.1",
                    "timestamp": datetime.utcnow().isoformat(),
                    "host_id": "test-host",
                    "details": {"src_port": 12345, "dst_port": 80, "protocol": "tcp"}
                },
                # Аутентификация
                {
                    "event_type": "auth.failure",
                    "src_ip": "10.0.0.50",
                    "timestamp": datetime.utcnow().isoformat(),
                    "host_id": "test-host",
                    "details": {"username": "admin", "reason": "invalid_password"}
                },
                # Процесс
                {
                    "event_type": "process.start",
                    "src_ip": "192.168.1.100",
                    "timestamp": datetime.utcnow().isoformat(),
                    "host_id": "test-host",
                    "details": {"process_name": "cmd.exe", "pid": 1234}
                }
            ]
            
            success_count = 0
            for i, event in enumerate(test_events, 1):
                print(f"  📝 Тестирую событие {i}: {event['event_type']}")
                try:
                    result = await self.process_event(event)
                    results_count = result.get('results_count', 0)
                    if result.get('event_processed', False):
                        self.log_test(f"Обработка события {i}", True, f"{results_count} правил сработало")
                        success_count += 1
                    else:
                        self.log_test(f"Обработка события {i}", False, "Событие не обработано")
                except Exception as e:
                    self.log_test(f"Обработка события {i}", False, f"Ошибка: {str(e)}")
            
            overall_success = success_count == len(test_events)
            self.log_test("Обработка событий", overall_success, f"{success_count}/{len(test_events)} событий обработано")
            return overall_success
            
        except Exception as e:
            self.log_test("Обработка событий", False, f"Ошибка: {str(e)}")
            return False
    
    async def test_threshold_rules(self) -> bool:
        """Тест правил порога"""
        print("\n[STATS] Тестирование правил порога...")
        
        try:
            # Отправить несколько событий для срабатывания порога
            threshold_reached = False
            for i in range(15):
                event = {
                    "event_type": "auth.failure",
                    "src_ip": "10.0.0.50",
                    "timestamp": datetime.utcnow().isoformat(),
                    "host_id": "test-host",
                    "details": {"username": "admin", "reason": "invalid_password"}
                }
                
                try:
                    result = await self.process_event(event)
                    if result.get('results_count', 0) > 0:
                        self.log_test("Правила порога", True, f"Порог достигнут после {i+1} событий")
                        threshold_reached = True
                        break
                except Exception as e:
                    print(f"    [WARNING] Ошибка при отправке события {i+1}: {e}")
                    continue
            
            if not threshold_reached:
                self.log_test("Правила порога", False, "Порог не достигнут после 15 событий")
            
            await asyncio.sleep(2)  # Дать время на обработку
            return threshold_reached
            
        except Exception as e:
            self.log_test("Правила порога", False, f"Ошибка: {str(e)}")
            return False
    
    async def test_correlation(self) -> bool:
        """Тест корреляции событий"""
        print("\n🔗 Тестирование корреляции...")
        
        try:
            # Создать связанные события
            events = [
                {"event_type": "net.connection", "src_ip": "192.168.1.100", "dst_ip": "192.168.1.1"},
                {"event_type": "auth.success", "src_ip": "192.168.1.100"},
                {"event_type": "process.start", "src_ip": "192.168.1.100"}
            ]
            
            success_count = 0
            for event in events:
                event.update({
                    "timestamp": datetime.utcnow().isoformat(),
                    "host_id": "test-host"
                })
                try:
                    result = await self.process_event(event)
                    if result.get('event_processed', False):
                        success_count += 1
                except Exception as e:
                    print(f"    [WARNING] Ошибка при отправке события: {e}")
            
            self.log_test("Отправка событий для корреляции", success_count == len(events), 
                         f"{success_count}/{len(events)} событий отправлено")
            
            await asyncio.sleep(5)  # Дать время на корреляцию
            
            # Проверить статистику
            try:
                stats = await self.get_stats()
                cache_size = stats.get('analyzer_stats', {}).get('event_cache_size', 0)
                self.log_test("Кеш событий", True, f"Событий в кеше: {cache_size}")
                return True
            except Exception as e:
                self.log_test("Кеш событий", False, f"Ошибка получения статистики: {e}")
                return False
            
        except Exception as e:
            self.log_test("Корреляция", False, f"Ошибка: {str(e)}")
            return False
    
    async def test_api_endpoints(self) -> bool:
        """Тест всех API эндпоинтов"""
        print("\n[NET] Тестирование API эндпоинтов...")
        
        try:
            endpoints = [
                ("GET", "/analyzer/status", "Статус анализатора"),
                ("GET", "/analyzer/health", "Здоровье системы"),
                ("GET", "/analyzer/config", "Конфигурация"),
                ("GET", "/analyzer/stats", "Статистика"),
                ("GET", "/health", "Общее здоровье"),
                ("GET", "/", "Корневой эндпоинт")
            ]
            
            success_count = 0
            for method, endpoint, description in endpoints:
                try:
                    if method == "GET":
                        async with self.session.get(f"{self.base_url}{endpoint}") as resp:
                            if resp.status == 200:
                                self.log_test(f"API {description}", True, f"Статус: {resp.status}")
                                success_count += 1
                            else:
                                self.log_test(f"API {description}", False, f"Статус: {resp.status}")
                    else:
                        # Для других методов можно добавить логику
                        pass
                except Exception as e:
                    self.log_test(f"API {description}", False, f"Ошибка: {str(e)}")
            
            overall_success = success_count == len(endpoints)
            self.log_test("API эндпоинты", overall_success, f"{success_count}/{len(endpoints)} эндпоинтов работают")
            return overall_success
            
        except Exception as e:
            self.log_test("API эндпоинты", False, f"Ошибка: {str(e)}")
            return False
    
    # API методы
    async def get_status(self) -> Dict[str, Any]:
        """Получить статус анализатора"""
        async with self.session.get(f"{self.base_url}/analyzer/status") as resp:
            return await resp.json()
    
    async def start_analyzer(self) -> Dict[str, Any]:
        """Запустить анализатор"""
        async with self.session.post(f"{self.base_url}/analyzer/start") as resp:
            return await resp.json()
    
    async def stop_analyzer(self) -> Dict[str, Any]:
        """Остановить анализатор"""
        async with self.session.post(f"{self.base_url}/analyzer/stop") as resp:
            return await resp.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверить здоровье системы"""
        async with self.session.get(f"{self.base_url}/analyzer/health") as resp:
            return await resp.json()
    
    async def get_rules(self) -> Dict[str, Any]:
        """Получить список правил"""
        async with self.session.get(f"{self.base_url}/analyzer/rules") as resp:
            return await resp.json()
    
    async def process_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Обработать событие"""
        async with self.session.post(f"{self.base_url}/analyzer/events/process", 
                                   json=event) as resp:
            return await resp.json()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Получить статистику"""
        async with self.session.get(f"{self.base_url}/analyzer/stats") as resp:
            return await resp.json()
    
    def print_summary(self):
        """Вывести сводку результатов тестирования"""
        print("\n" + "="*60)
        print("[STATS] СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Всего тестов: {total_tests}")
        print(f"[OK] Успешно: {passed_tests}")
        print(f"[ERROR] Провалено: {failed_tests}")
        print(f"📈 Успешность: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n[ERROR] ПРОВАЛЕННЫЕ ТЕСТЫ:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n" + "="*60)
        
        return failed_tests == 0


async def main():
    """Основная функция тестирования"""
    print("[START] Запуск автоматизированного тестирования SIEM Analyzer...")
    print(f"⏰ Время начала: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Проверить аргументы командной строки
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"[NET] Тестирую API по адресу: {base_url}")
    
    async with AnalyzerTester(base_url) as tester:
        # Тест 1: API эндпоинты
        await tester.test_api_endpoints()
        
        # Тест 2: Жизненный цикл
        await tester.test_analyzer_lifecycle()
        
        # Тест 3: Обработка событий
        await tester.test_event_processing()
        
        # Тест 4: Правила порога
        await tester.test_threshold_rules()
        
        # Тест 5: Корреляция
        await tester.test_correlation()
    
    # Вывести сводку
    all_tests_passed = tester.print_summary()
    
    if all_tests_passed:
        print("[SUCCESS] Все тесты прошли успешно!")
        return 0
    else:
        print("💥 Некоторые тесты провалились!")
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[WARNING] Тестирование прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        sys.exit(1)
