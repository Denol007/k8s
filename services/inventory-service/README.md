# Inventory Service

Сервис управления складским учетом, резервированием товаров и отслеживанием остатков.

## Версия
1.0.0

## Порт
5007

## Функциональность

- ✅ Проверка наличия товаров
- ✅ Резервирование товаров для заказов
- ✅ Освобождение резерва при отмене заказа
- ✅ Обновление складских остатков
- ✅ Добавление новых товаров
- ✅ Мониторинг низких остатков
- ✅ Статистика по инвентарю

## Endpoints

### Health & Readiness
- `GET /health` - Health check
- `GET /ready` - Readiness check

### Inventory Management

#### Список всего инвентаря
```http
GET /inventory
```

#### Проверить наличие товара
```http
GET /inventory/{product_id}
```

Ответ:
```json
{
  "product_id": "PROD-001",
  "name": "Laptop",
  "total_quantity": 50,
  "reserved": 5,
  "available": 45,
  "price": 999.99,
  "in_stock": true
}
```

#### Зарезервировать товар
```http
POST /inventory/{product_id}/reserve
Content-Type: application/json

{
  "quantity": 2,
  "order_id": "ORD-12345"
}
```

#### Освободить резерв (отмена заказа)
```http
POST /inventory/{product_id}/release
Content-Type: application/json

{
  "quantity": 2,
  "order_id": "ORD-12345"
}
```

#### Обновить количество на складе
```http
PUT /inventory/{product_id}
Content-Type: application/json

{
  "quantity": 100,
  "price": 899.99
}
```

#### Добавить новый товар
```http
POST /inventory
Content-Type: application/json

{
  "product_id": "PROD-006",
  "name": "Webcam",
  "quantity": 80,
  "price": 59.99
}
```

#### Товары с низким остатком
```http
GET /inventory/low-stock?threshold=20
```

#### Статистика
```http
GET /stats
```

Ответ:
```json
{
  "total_products": 5,
  "total_items": 575,
  "total_reserved": 33,
  "total_available": 542,
  "total_inventory_value": 152497.25
}
```

## Интеграция с другими сервисами

### Order Service
При создании заказа резервируем товары:
```python
# В Order Service
response = requests.post(
    'http://inventory-service:5007/inventory/PROD-001/reserve',
    json={'quantity': 2, 'order_id': order_id}
)
if response.status_code == 200:
    # Резерв успешен, продолжаем создание заказа
else:
    # Недостаточно товара
```

При отмене заказа освобождаем:
```python
requests.post(
    'http://inventory-service:5007/inventory/PROD-001/release',
    json={'quantity': 2, 'order_id': order_id}
)
```

### Notification Service
При низких остатках отправляем уведомление:
```python
low_stock = requests.get('http://inventory-service:5007/inventory/low-stock').json()
if low_stock['low_stock_count'] > 0:
    requests.post('http://notification-service:5004/send', json={
        'type': 'low_stock_alert',
        'items': low_stock['items']
    })
```

## Локальный запуск

```bash
cd services/inventory-service
pip install -r requirements.txt
python app.py
```

## Тестирование

```bash
# Проверить наличие
curl http://localhost:5007/inventory/PROD-001

# Зарезервировать
curl -X POST http://localhost:5007/inventory/PROD-001/reserve \
  -H "Content-Type: application/json" \
  -d '{"quantity": 2, "order_id": "ORD-123"}'

# Низкие остатки
curl http://localhost:5007/inventory/low-stock?threshold=50

# Статистика
curl http://localhost:5007/stats
```

## Метрики Prometheus
- `/metrics` - Prometheus метрики

## CI/CD & GitOps

При push в Git:
1. GitHub Actions собирает Docker образ
2. Образ пушится в DockerHub
3. Обновляется `helm/values/inventory-service.yaml`
4. **Argo CD автоматически деплоит в кластер!** 🚀

## Переменные окружения
- `PORT` - Порт сервиса (по умолчанию: 5007)
