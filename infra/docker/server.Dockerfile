# infra/docker/server.Dockerfile
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Копируем зависимости
COPY backend/requirements.txt /app/requirements.txt

# Устанавливаем Python зависимости
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Копируем код
COPY backend /app/backend
COPY db /app/db

# Кладем офлайн-артефакты (репозитории) внутрь образа, чтобы раздавать их локально без интернета
# Ожидается, что каталоги/архивы будут находиться в папке offline_repos рядом с корнем проекта
COPY offline_repos /app/offline_repos

# Создаем директорию для состояния с правильными правами
RUN mkdir -p /app/backend/analyzer/.state && \
    chmod 755 /app/backend/analyzer/.state

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 backend && \
    chown -R backend:backend /app

USER backend

# Проверяем работоспособность
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

EXPOSE 8000

# Запускаем сервер
CMD ["uvicorn", "backend.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
