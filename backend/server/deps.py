from contextlib import contextmanager
from typing import Annotated
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy import text
from ..common.db import get_session

@contextmanager
def db_session():
    """Зависимость FastAPI: выдаёт SQLAlchemy-сессию."""
    with get_session() as s:
        yield s

async def get_current_user_from_api_key(x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None):
    """Получение user_id по API ключу для фильтрации данных"""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key header missing",
        )

    with get_session() as s:
        # Получаем все активные хеши токенов
        hashes = s.execute(text(
            """
            SELECT user_id, token_hash FROM security_system.api_keys
            WHERE revoked_at IS NULL
            """
        )).fetchall()

        # Проверяем предоставленный ключ по каждому хешу
        import bcrypt
        for user_id, token_hash in hashes:
            if bcrypt.checkpw(x_api_key.encode(), token_hash.encode()):
                return user_id

        # Если ни один ключ не подошел
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

def get_current_user():
    """Получение текущего пользователя из контекста запроса"""
    # В реальной реализации здесь будет извлечение пользователя из JWT токена
    # или из сессии. Пока что возвращаем None для совместимости
    return None

def get_db():
    """Зависимость для получения сессии базы данных"""
    with get_session() as s:
        yield s
