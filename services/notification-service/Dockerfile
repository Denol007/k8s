FROM python:3.11-slim

LABEL maintainer="Denol007"
LABEL service="notification-service"
LABEL version="1.0.0"

WORKDIR /app

# Установить зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопировать код приложения
COPY . .

# Создать непривилегированного пользователя
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Переключиться на непривилегированного пользователя
USER appuser

# Открыть порт
EXPOSE 5004

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5004/health')"

# Запустить приложение с Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5004", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
