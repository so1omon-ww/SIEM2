import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Берём строку подключения из .env (pydantic-settings уже загружает её в settings),
# но оставим fallback на переменную окружения для простоты.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/security_system",
)

# Engine: future=True — стиль SQLA 2.x; pool_pre_ping — автопроврека соединений
engine = create_engine(DATABASE_URL, pool_pre_ping=True,
               connect_args={"options": "-c search_path=security_system,public"})

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

@contextmanager
def get_session():
    """Контекстный менеджер сессии БД."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_db():
    """Dependency для FastAPI для получения сессии БД."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()