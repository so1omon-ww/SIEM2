import os
import secrets
import logging
import hashlib
from sqlalchemy import text
from ...common.db import get_session

LOG = logging.getLogger("auth_service")

def verify_token(agent_id: str, token: str) -> bool:
    """
    Простая проверка токена агента.
    Источник токена:
      1) переменная окружения AGENT_TOKEN_<AGENT_ID>
      2) единый токен из AGENT_TOKEN (на всех)
      3) пусто -> False
    """
    if not agent_id or not token:
        return False

    env_key = f"AGENT_TOKEN_{agent_id}".upper().replace("-", "_")
    expected = os.environ.get(env_key) or os.environ.get("AGENT_TOKEN")
    if expected is None:
        LOG.debug("No token configured for %s", agent_id)
        return False

    ok = secrets.compare_digest(str(expected), str(token))
    if not ok:
        LOG.warning("Token mismatch for %s", agent_id)
    return ok


def get_user_id_by_api_key(raw_token: str) -> int | None:
    """Возвращает user_id по API ключу (прямое сравнение и ключ не отозван)."""
    if not raw_token:
        return None
    with get_session() as s:
        row = s.execute(text(
            """
            SELECT user_id FROM security_system.api_keys
            WHERE token = :token AND revoked_at IS NULL
            LIMIT 1
            """
        ), {"token": raw_token}).first()
        return int(row[0]) if row else None
