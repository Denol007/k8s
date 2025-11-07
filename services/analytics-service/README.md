# Analytics Service

Сервис для сбора и анализа данных о действиях пользователей.

## Версия
1.0.0

## Порт
5005

## Endpoints

### Health & Readiness
- `GET /health` - Health check endpoint
- `GET /ready` - Readiness check endpoint

### Tracking
- `POST /track/view` - Отслеживание просмотра страницы
  ```json
  {
    "user_id": "user123",
    "page": "/products/123",
    "timestamp": "2024-01-15T10:30:00Z"
  }
  ```

- `POST /track/click` - Отслеживание кликов
  ```json
  {
    "user_id": "user123",
    "element": "buy-button",
    "page": "/products/123",
    "timestamp": "2024-01-15T10:31:00Z"
  }
  ```

### Statistics
- `GET /stats` - Получение общей статистики
  ```json
  {
    "total_views": 1523,
    "total_clicks": 342,
    "unique_users": 145
  }
  ```

- `GET /stats/report` - Детальный отчет
  ```json
  {
    "views_by_page": {
      "/products/123": 45,
      "/products/456": 32
    },
    "clicks_by_element": {
      "buy-button": 23,
      "add-to-cart": 19
    }
  }
  ```

## Метрики Prometheus
- `/metrics` - Prometheus метрики

## Локальный запуск

### Через Python
```bash
cd services/analytics-service
pip install -r requirements.txt
python app.py
```

### Через Docker
```bash
docker build -t analytics-service:latest .
docker run -p 5005:5005 analytics-service:latest
```

## Переменные окружения
- `PORT` - Порт сервиса (по умолчанию: 5005)

## Зависимости
- Flask 3.0.0
- prometheus-flask-exporter 0.23.0
- gunicorn 21.2.0

## CI/CD
Автоматическая сборка и деплой через GitHub Actions при push в ветку `feature/*` или `main`.
