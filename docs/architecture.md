# Architecture Documentation

## Обзор системы

Микросервисная e-commerce платформа состоит из 4 основных сервисов, каждый из которых отвечает за свою бизнес-логику.

## Микросервисы

### 1. User Service (Порт 5000)
**Назначение:** Управление пользователями и аутентификация

**Endpoints:**
- `POST /api/v1/users/register` - Регистрация пользователя
- `POST /api/v1/users/login` - Вход в систему (возвращает JWT токен)
- `GET /api/v1/users/{id}` - Получение информации о пользователе
- `GET /api/v1/users` - Список всех пользователей

**База данных:** PostgreSQL (userdb)
- Таблица: users (id, username, email, password_hash, created_at)

**Зависимости:**
- PostgreSQL
- Vault (для JWT секретов)

### 2. Product Service (Порт 5001)
**Назначение:** Управление каталогом продуктов

**Endpoints:**
- `GET /api/v1/products` - Список продуктов (с пагинацией)
- `GET /api/v1/products/{id}` - Информация о продукте
- `POST /api/v1/products` - Создание продукта
- `PUT /api/v1/products/{id}` - Обновление продукта
- `DELETE /api/v1/products/{id}` - Удаление продукта
- `PATCH /api/v1/products/{id}/stock` - Обновление остатков

**База данных:** PostgreSQL (productdb)
- Таблица: products (id, name, description, price, stock, category, created_at, updated_at)

**Зависимости:**
- PostgreSQL

### 3. Order Service (Порт 5002)
**Назначение:** Управление заказами

**Endpoints:**
- `POST /api/v1/orders` - Создание заказа
- `GET /api/v1/orders/{id}` - Информация о заказе
- `GET /api/v1/orders/user/{user_id}` - Заказы пользователя
- `PATCH /api/v1/orders/{id}/status` - Обновление статуса заказа
- `POST /api/v1/orders/{id}/cancel` - Отмена заказа

**База данных:** PostgreSQL (orderdb)
- Таблица: orders (id, user_id, product_id, quantity, total_price, status, payment_id, created_at, updated_at)

**Зависимости:**
- PostgreSQL
- Product Service (проверка наличия товара)
- Payment Service (обработка платежей)

### 4. Payment Service (Порт 5003)
**Назначение:** Обработка платежей

**Endpoints:**
- `POST /api/v1/payments` - Создание платежа
- `GET /api/v1/payments/{payment_id}` - Информация о платеже
- `POST /api/v1/payments/{payment_id}/process` - Обработка платежа
- `POST /api/v1/payments/{payment_id}/refund` - Возврат средств
- `GET /api/v1/payments/user/{user_id}` - Платежи пользователя
- `GET /api/v1/payments/order/{order_id}` - Платеж по заказу

**База данных:** PostgreSQL (paymentdb)
- Таблица: payments (id, payment_id, order_id, user_id, amount, currency, status, payment_method, transaction_id, created_at, updated_at)

**Зависимости:**
- PostgreSQL

## Инфраструктура

### AWS EKS Cluster
- **Nodes:** 2-10 t3.medium instances (auto-scaling)
- **Kubernetes Version:** 1.28
- **Networking:** VPC with 3 availability zones

### Database
- **Primary:** RDS PostgreSQL 15.4 (db.t3.medium)
- **Replica:** Read replica for analytics
- **Backup:** 7-day retention
- **Storage:** 100GB with auto-scaling

### Networking
```
Internet
    ↓
ALB/Ingress
    ↓
┌─────────────────────────────────┐
│  Kubernetes Ingress (NGINX)     │
└─────────────────────────────────┘
    ↓
┌──────────┬──────────┬──────────┬──────────┐
│   User   │ Product  │  Order   │ Payment  │
│ Service  │ Service  │ Service  │ Service  │
└──────────┴──────────┴──────────┴──────────┘
    ↓           ↓           ↓           ↓
┌────────────────────────────────────────────┐
│           PostgreSQL RDS                    │
└────────────────────────────────────────────┘
```

## Безопасность

### RBAC
- Namespace-level изоляция
- ServiceAccounts для каждого сервиса
- Минимальные привилегии (least privilege)

### Vault
- Централизованное управление секретами
- Динамические credentials для БД
- JWT секреты для аутентификации
- Автоматическая ротация секретов

### Network Policies
- Ограничение трафика между сервисами
- Доступ к БД только из приватных подсетей

## Мониторинг

### Prometheus
**Метрики:**
- HTTP requests (rate, duration, errors)
- CPU/Memory usage
- Database connections
- Custom business metrics

**Алерты:**
- High error rate (>5% за 5 минут)
- High latency (p95 >1s)
- Pod not ready
- High CPU/Memory usage (>90%)
- Service down

### Grafana
**Dashboards:**
- Cluster overview
- Per-service metrics
- Database performance
- Business KPIs

## Логирование

### ELK Stack
- **Elasticsearch:** Хранение логов (30 дней retention)
- **Fluentd:** Сбор логов со всех подов
- **Kibana:** Визуализация и поиск

**Log format:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "INFO",
  "service": "user-service",
  "pod": "user-service-7d8f9c-abc123",
  "message": "User logged in: john_doe",
  "user_id": 123,
  "request_id": "req-abc-123"
}
```

## CI/CD Pipeline

### Build Stage
1. Checkout code
2. Run linters (flake8)
3. Run unit tests
4. Build Docker image
5. Scan for vulnerabilities (Trivy)
6. Push to Docker Hub

### Deploy Stage
1. Update kubectl config
2. Deploy to Kubernetes
3. Wait for rollout
4. Run smoke tests
5. Notify Slack

### Rollback
Автоматический rollback при failed deployment:
```bash
kubectl rollout undo deployment/service-name
```

## Масштабирование

### Horizontal Pod Autoscaler (HPA)
- Min replicas: 2
- Max replicas: 10
- Target CPU: 70%
- Target Memory: 80%

### Cluster Autoscaler
Автоматическое добавление nodes при нехватке ресурсов

## High Availability

### Service Level
- Минимум 2 реплики каждого сервиса
- Health checks (liveness, readiness)
- Rolling updates (max unavailable: 1)

### Database Level
- Multi-AZ deployment
- Automated backups
- Read replica для отказоустойчивости

### Ingress Level
- Multiple ingress controllers
- SSL/TLS termination
- Rate limiting

## Disaster Recovery

### Backup Strategy
- Database: Automated daily backups (7 days)
- Kubernetes configs: Git repository
- Secrets: Vault backup

### Recovery Time Objectives
- RTO (Recovery Time Objective): 1 hour
- RPO (Recovery Point Objective): 15 minutes

## Performance

### Expected Load
- 10,000 requests/second peak
- 100ms p95 latency
- 99.9% uptime SLA

### Caching Strategy
- Application level: Redis (future)
- Database level: Query result cache
- CDN: Static assets

## Future Improvements

1. **Service Mesh** - Istio для advanced traffic management
2. **Message Queue** - RabbitMQ/Kafka для async communication
3. **Caching** - Redis для улучшения производительности
4. **API Gateway** - Kong/Ambassador для centralized routing
5. **Distributed Tracing** - Jaeger для request tracing
6. **GraphQL API** - Для более гибкого API
