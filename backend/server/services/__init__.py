# делает удобные импорты сервиса на уровень пакета
from .ingest_service import ingest_event
from .event_service import save_event
from .alert_service import raise_alert, maybe_raise_alert
from .auth_service import verify_token
