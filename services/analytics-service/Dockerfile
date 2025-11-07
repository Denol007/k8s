FROM python:3.11-slim

# Метаданные
LABEL maintainer="denol007@github.com"
LABEL service="analytics-service"
LABEL version="1.0.0"

# Рабочая директория
WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание непривилегированного пользователя
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Порт
EXPOSE 5005

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5005/health')" || exit 1

# Запуск
CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--workers", "4", "--timeout", "60", "app:app"]
