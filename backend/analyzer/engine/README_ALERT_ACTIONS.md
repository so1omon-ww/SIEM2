# Система действий по алертам безопасности

## Обзор

Система действий по алертам предоставляет автоматизированные и полуавтоматические меры противодействия различным типам сетевых атак. Система поддерживает следующие типы атак:

- **DDoS атаки** (SYN-флуд, HTTP RPS)
- **Сканирование портов** (вертикальное и горизонтальное)
- **Брутфорс атаки** (SSH, HTTP, RDP)
- **ARP-спуфинг** и ARP-флуд
- **DNS атаки** (NXDOMAIN-флуд, случайные поддомены)
- **Латеральное перемещение** в сети
- **Аномальная активность**

## Архитектура

### Основные компоненты

1. **AlertActionEngine** - основной движок обработки действий
2. **AlertContext** - контекст алерта с метаданными
3. **ActionConfig** - конфигурация действий для каждого типа алерта
4. **API endpoints** - REST API для управления действиями

### Типы действий

- `block_ip` - блокировка IP адреса
- `rate_limit` - ограничение скорости запросов
- `isolate_host` - изоляция хоста в карантинный VLAN
- `restart_service` - перезапуск сервиса
- `flush_cache` - очистка кеша (ARP, DNS)
- `notify_admin` - уведомление администратора
- `log_event` - логирование события
- `custom_script` - выполнение пользовательского скрипта

## Конфигурация

### Настройка действий по умолчанию

Система поставляется с предустановленными конфигурациями действий для каждого типа алерта:

```python
# DDoS SYN-флуд
self.action_configs[AlertType.DDOS_SYN_FLOOD] = [
    ActionConfig(
        action_type=ActionType.RATE_LIMIT,
        auto_execute=True,
        ttl_minutes=30,
        parameters={"max_connections_per_second": 10}
    ),
    ActionConfig(
        action_type=ActionType.BLOCK_IP,
        auto_execute=False,  # Требует подтверждения
        ttl_minutes=60,
        conditions=["confidence > 0.9"]
    )
]
```

### Условия выполнения

Действия могут выполняться с условиями:

```python
conditions = [
    "confidence > 0.9",  # Уверенность выше 90%
    "severity == 'critical'",  # Критический уровень
    "source_ip != '192.168.1.0/24'"  # Исключение внутренних сетей
]
```

## API Endpoints

### Обработка алертов

```http
POST /api/alert-actions/process-alert
Content-Type: application/json

{
  "alert_type": "ddos_syn_flood",
  "source_ip": "192.168.1.100",
  "target_ip": "10.0.0.1",
  "severity": "high",
  "confidence": 0.95
}
```

### Управление конфигурациями

```http
GET /api/alert-actions/action-configs
PUT /api/alert-actions/action-configs/{alert_type}
```

### Мониторинг

```http
GET /api/alert-actions/active-blocks
GET /api/alert-actions/action-history
GET /api/alert-actions/pending-actions
```

## Интеграция с правилами анализатора

### YAML конфигурация правил

```yaml
ddos_syn_flood:
  description: "Обнаружение DDoS атак с использованием SYN-флуда"
  enabled: true
  severity: high
  thresholds:
    syn_packets_per_second: 200
    syn_ack_ratio_min: 3.0
    time_window_seconds: 10
  actions:
    - "rate_limit"
    - "block_ip"
    - "notify_admin"
  parameters:
    rate_limit:
      max_connections_per_second: 10
      ttl_minutes: 30
    block_ip:
      ttl_minutes: 60
      conditions: ["confidence > 0.9"]
```

## Безопасность

### Режимы работы

1. **Alert-only** - только уведомления, без автоматических действий
2. **Semi-automatic** - действия требуют подтверждения
3. **Fully automatic** - полная автоматизация (осторожно!)

### Защитные механизмы

- **TTL для блокировок** - автоматическое снятие блокировок
- **Allowlist** - исключения для доверенных IP
- **Rate limiting** - ограничение частоты действий
- **Audit log** - полное логирование всех действий

## Мониторинг и логирование

### Метрики

- Количество выполненных действий по типам
- Время отклика системы
- Количество ложных срабатываний
- Эффективность мер противодействия

### Логи

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "block_ip",
  "context": {
    "alert_type": "ddos_syn_flood",
    "source_ip": "192.168.1.100",
    "severity": "high"
  },
  "status": "success",
  "details": "Blocked IP 192.168.1.100 for 60 minutes"
}
```

## Расширение системы

### Добавление новых типов действий

1. Добавить новый `ActionType` в enum
2. Реализовать метод в `AlertActionEngine`
3. Обновить API endpoints
4. Добавить UI компоненты

### Пользовательские скрипты

```python
# Скрипт получает контекст через переменные окружения
import os

alert_type = os.environ.get('ALERT_TYPE')
source_ip = os.environ.get('SOURCE_IP')
severity = os.environ.get('SEVERITY')

# Ваша логика обработки
```

## Примеры использования

### Блокировка подозрительного IP

```python
context = AlertContext(
    alert_type=AlertType.PORT_SCAN,
    source_ip="192.168.1.100",
    severity=ActionSeverity.HIGH,
    confidence=0.9
)

actions = await alert_action_engine.process_alert(context)
```

### Настройка уведомлений

```python
# Slack уведомление
async def notify_admin_slack(context: AlertContext):
    webhook_url = "https://hooks.slack.com/..."
    message = f"🚨 Security Alert: {context.alert_type.value} from {context.source_ip}"
    # Отправка в Slack
```

## Troubleshooting

### Частые проблемы

1. **Действия не выполняются**
   - Проверьте условия выполнения
   - Убедитесь, что действие включено
   - Проверьте права доступа для системных команд

2. **Ложные срабатывания**
   - Настройте allowlist для внутренних сетей
   - Увеличьте пороги срабатывания
   - Добавьте дополнительные условия

3. **Производительность**
   - Используйте асинхронную обработку
   - Ограничьте частоту выполнения действий
   - Мониторьте использование ресурсов

### Логи для отладки

```bash
# Просмотр логов действий
tail -f /var/log/siem/alert_actions.log

# Проверка активных блокировок
curl http://localhost:8000/api/alert-actions/active-blocks

# История действий
curl http://localhost:8000/api/alert-actions/action-history?limit=50
```
