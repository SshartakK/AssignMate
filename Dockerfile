# Базовый образ Python
FROM python:3.12.6-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Создаем и настраиваем не-root пользователя
RUN useradd -m myuser

# Создаем рабочие директории с правильными правами
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R myuser:myuser /app && \
    chmod -R 755 /app

WORKDIR /app

# Копируем зависимости
COPY --chown=myuser:myuser requirements.txt .

# Устанавливаем зависимости Python и uvicorn
RUN pip install --no-cache-dir uvicorn && \
    pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY --chown=myuser:myuser . .

# Переключаемся на не-root пользователя
USER myuser

# Устанавливаем рабочую директорию
WORKDIR /app/AssignMate

# Создаем директорию для статики и настраиваем права
RUN mkdir -p /app/staticfiles && \
    chown -R myuser:myuser /app/staticfiles && \
    chmod -R 755 /app/staticfiles

# Собираем статические файлы
RUN python manage.py collectstatic --noinput --clear

# Открываем порт
EXPOSE 8000

# Команда для запуска приложения
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "AssignMate.asgi:application"]