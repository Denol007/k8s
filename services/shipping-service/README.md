# Shipping Service

Сервис для управления доставкой заказов, отслеживания отправлений и расчета стоимости доставки.

## Версия
1.0.0

## Порт
5006

## Функциональность

- ✅ Создание отправлений
- ✅ Отслеживание статуса доставки
- ✅ Расчет стоимости и сроков доставки
- ✅ Интеграция с несколькими службами доставки
- ✅ История изменений статусов
- ✅ Отмена отправлений
- ✅ Статистика по доставкам

## Endpoints

### Health & Readiness
- `GET /health` - Health check
- `GET /ready` - Readiness check
- `GET /` - Информация о сервисе и endpoints

### Shipments (Отправки)

#### Создать отправку
```http
POST /shipment
Content-Type: application/json

{
  "order_id": "ORD-123456",
  "recipient": "John Doe",
  "address": {
    "street": "123 Main St",
    "city": "New York",
    "state": "NY",
    "zip": "10001",
    "country": "USA"
  },
  "items": [
    {
      "name": "Product A",
      "quantity": 2,
      "weight": 1.5
    }
  ]
}
```

Ответ:
```json
{
  "message": "Shipment created successfully",
  "shipment": {
    "shipment_id": "SHIP-000001",
    "order_id": "ORD-123456",
    "tracking_number": "DHL1234567",
    "carrier": "DHL Express",
    "status": "pending",
    "estimated_delivery": "2025-11-14T10:00:00Z",
    ...
  }
}
```

#### Получить отправку
```http
GET /shipment/{shipment_id}
```

#### Обновить статус
```http
PUT /shipment/{shipment_id}/status
Content-Type: application/json

{
  "status": "in_transit",
  "location": "Distribution Center NYC",
  "note": "Package sorted and ready for delivery"
}
```

Возможные статусы:
- `pending` - Ожидает обработки
- `preparing` - Подготовка к отправке
- `in_transit` - В пути
- `out_for_delivery` - Передано курьеру
- `delivered` - Доставлено
- `cancelled` - Отменено

#### Отследить отправку
```http
GET /shipment/{shipment_id}/track
```

Ответ:
```json
{
  "shipment_id": "SHIP-000001",
  "tracking_number": "DHL1234567",
  "carrier": "DHL Express",
  "status": "in_transit",
  "estimated_delivery": "2025-11-14T10:00:00Z",
  "history": [
    {
      "status": "pending",
      "timestamp": "2025-11-07T10:00:00Z",
      "location": "Warehouse",
      "note": "Shipment created"
    },
    {
      "status": "preparing",
      "timestamp": "2025-11-07T12:00:00Z",
      "location": "Warehouse",
      "note": "Package prepared"
    }
  ]
}
```

#### Список отправок
```http
GET /shipments?status=in_transit&order_id=ORD-123456
```

#### Отменить отправку
```http
DELETE /shipment/{shipment_id}
```

### Estimates (Расчеты)

#### Рассчитать стоимость доставки
```http
POST /estimate
Content-Type: application/json

{
  "from_address": {
    "city": "New York",
    "zip": "10001"
  },
  "to_address": {
    "city": "Los Angeles",
    "zip": "90001"
  },
  "weight": 2.5,
  "dimensions": {
    "length": 30,
    "width": 20,
    "height": 15
  }
}
```

Ответ:
```json
{
  "estimates": [
    {
      "carrier": "USPS Priority",
      "cost": 25.50,
      "currency": "USD",
      "estimated_days": 3,
      "estimated_delivery": "2025-11-10T10:00:00Z"
    },
    {
      "carrier": "DHL Express",
      "cost": 32.00,
      "currency": "USD",
      "estimated_days": 2,
      "estimated_delivery": "2025-11-09T10:00:00Z"
    }
  ],
  "calculated_at": "2025-11-07T10:00:00Z"
}
```

### Statistics

#### Статистика
```http
GET /stats
```

Ответ:
```json
{
  "total_shipments": 150,
  "by_status": {
    "delivered": 85,
    "in_transit": 40,
    "preparing": 15,
    "pending": 10
  },
  "by_carrier": {
    "DHL Express": 50,
    "FedEx International": 40,
    "UPS Worldwide": 35,
    "USPS Priority": 25
  }
}
```

## Метрики Prometheus
- `/metrics` - Prometheus метрики

## Поддерживаемые службы доставки

- DHL Express
- FedEx International
- UPS Worldwide
- USPS Priority
- Local Courier

## Локальный запуск

### Через Python
```bash
cd services/shipping-service
pip install -r requirements.txt
python app.py
```

### Через Docker
```bash
docker build -t shipping-service:latest .
docker run -p 5006:5006 shipping-service:latest
```

### Тестирование
```bash
# Создать отправку
curl -X POST http://localhost:5006/shipment \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORD-123",
    "recipient": "John Doe",
    "address": {"street": "123 Main St", "city": "NYC"},
    "items": [{"name": "Product", "quantity": 1, "weight": 1.0}]
  }'

# Отследить отправку
curl http://localhost:5006/shipment/SHIP-000001/track

# Получить статистику
curl http://localhost:5006/stats
```

## Переменные окружения
- `PORT` - Порт сервиса (по умолчанию: 5006)

## Зависимости
- Flask 3.0.0
- prometheus-flask-exporter 0.23.0
- gunicorn 21.2.0
- requests 2.31.0

## Интеграция с другими сервисами

### Order Service
При создании заказа (Order Service) автоматически создается отправка:
```python
# В Order Service после создания заказа
response = requests.post('http://shipping-service:5006/shipment', json={
    'order_id': order_id,
    'recipient': customer_name,
    'address': delivery_address,
    'items': order_items
})
```

### Notification Service
При изменении статуса отправки отправляется уведомление:
```python
# После обновления статуса
requests.post('http://notification-service:5004/send', json={
    'type': 'shipping_update',
    'recipient': customer_email,
    'data': {
        'tracking_number': tracking_number,
        'status': new_status
    }
})
```

## CI/CD
Автоматическая сборка и деплой через GitHub Actions при push в ветку.

## Деплой через Helm
```bash
./scripts/helm-deploy.sh shipping-service
```
