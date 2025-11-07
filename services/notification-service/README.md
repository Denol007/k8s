# Notification Service

Сервис для отправки уведомлений (email, SMS, push notifications).

## Endpoints

- `GET /` - Информация о сервисе
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `POST /send` - Отправить уведомление
- `GET /notifications` - Список уведомлений
- `GET /metrics` - Prometheus metrics

## Использование

### Отправить уведомление

```bash
curl -X POST http://localhost:5004/send \
  -H "Content-Type: application/json" \
  -d '{
    "recipient": "user@example.com",
    "message": "Hello from notification service!",
    "type": "email"
  }'
```

### Health check

```bash
curl http://localhost:5004/health
```

## Локальная разработка

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить
python app.py

# Или с Gunicorn
gunicorn --bind 0.0.0.0:5004 --workers 4 app:app
```

## Docker

```bash
# Собрать
docker build -t denol007/notification-service:latest .

# Запустить
docker run -p 5004:5004 denol007/notification-service:latest
```

## Kubernetes

Манифесты генерируются автоматически через CI/CD при push в репозиторий.

Или вручную:
```bash
./scripts/generate-k8s-manifests.sh notification-service 5004 2
```

## Переменные окружения

- `SERVICE_NAME` - Имя сервиса (default: notification-service)
- `PORT` - Порт (default: 5004)
- `ENVIRONMENT` - Окружение (development/production)
- `LOG_LEVEL` - Уровень логирования (INFO/DEBUG/WARNING/ERROR)
