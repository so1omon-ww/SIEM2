import asyncio, logging
from datetime import datetime, timezone
from typing import Callable, Any

log = logging.getLogger("analyzer.runner")

async def run_loop(db_provider: Callable[[], Any], interval_sec: int = 30):
    """
    Основной цикл анализатора.
    Периодически проверяет события за последние N минут и применяет threshold-правила.
    """
    log.info("Analyzer runner started, interval=%ss", interval_sec)
    
    try:
        from .evaluator import load_ruleset, evaluate_window
        rules = load_ruleset()
        log.info("Loaded %d rules", len(rules))
    except Exception as e:
        log.error("Failed to load rules: %s", e)
        return
    
    while True:
        try:
            # Получаем сессию БД
            db = await db_provider()
            
            # Применяем threshold-правила к событиям за последние 15 минут
            try:
                created = await evaluate_window(db, rules, None, datetime.now(timezone.utc))
                if created > 0:
                    log.info("Created %d alerts from threshold rules", created)
            except Exception as e:
                log.error("Threshold evaluation failed: %s", e)
            
            # Закрываем сессию
            if hasattr(db, 'close'):
                db.close()
            elif hasattr(db, '__exit__'):
                await db.__aexit__(None, None, None)
                
        except Exception as e:
            log.exception("Runner cycle error: %s", e)
        
        # Ждем следующего цикла
        await asyncio.sleep(interval_sec)
