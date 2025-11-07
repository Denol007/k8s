FROM python:3.11-slim

LABEL maintainer="denol007@github.com"
LABEL service="inventory-service"
LABEL version="1.0.0"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5007

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5007/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:5007", "--workers", "4", "--timeout", "60", "app:app"]
